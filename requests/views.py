from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

import auditlog.models as auditlog
from bloodbank.constants import BLOOD_GROUPS
from inventory.services import issue_units

from .forms import BloodRequestForm, IssueForm, ReviewForm
from .models import BloodIssue, BloodRequest


def request_create(request):
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save()
            auditlog.record(
                auditlog.AuditLog.Action.REQUEST_SUBMITTED,
                entity_type="bloodrequest",
                entity_id=blood_request.tracking_id,
                new_value=f"{blood_request.quantity}u {blood_request.blood_group} for {blood_request.hospital_name}",
            )
            messages.success(request, 'Your blood request was submitted for review.')
            return redirect('requests:detail', tracking_id=blood_request.tracking_id)
    else:
        form = BloodRequestForm()
    return render(request, 'requests/request_form.html', {'form': form})


def request_detail(request, tracking_id):
    blood_request = get_object_or_404(BloodRequest, tracking_id=tracking_id)
    return render(request, 'requests/request_detail.html', {'blood_request': blood_request})


def is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff)
def request_queue(request):
    """Staff request queue with search/filter (Part 3.E 'add useful request search/filter functionality')."""
    status = request.GET.get("status", "").strip()
    blood_group = request.GET.get("blood_group", "").strip()
    hospital = request.GET.get("hospital", "").strip()

    requests_qs = BloodRequest.objects.select_related('reviewed_by', 'issue_transaction')
    if status in dict(BloodRequest.Status.choices):
        requests_qs = requests_qs.filter(status=status)
    if blood_group in BLOOD_GROUPS:
        requests_qs = requests_qs.filter(blood_group=blood_group)
    if hospital:
        requests_qs = requests_qs.filter(hospital_name__icontains=hospital)

    paginator = Paginator(requests_qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        'requests/request_queue.html',
        {
            "page_obj": page_obj,
            "requests": page_obj.object_list,
            "status": status,
            "blood_group": blood_group,
            "hospital": hospital,
            "status_choices": BloodRequest.Status.choices,
            "blood_groups": BLOOD_GROUPS,
        },
    )


@user_passes_test(is_staff)
def request_review(request, tracking_id):
    blood_request = get_object_or_404(BloodRequest, tracking_id=tracking_id)
    if request.method != 'POST':
        return redirect('requests:queue')

    form = ReviewForm(request.POST)
    if form.is_valid() and blood_request.status == BloodRequest.Status.PENDING:
        blood_request.status = form.cleaned_data['action']
        blood_request.review_note = form.cleaned_data['review_note']
        blood_request.reviewed_by = request.user
        blood_request.reviewed_at = timezone.now()
        blood_request.save(update_fields=(
            'status', 'review_note', 'reviewed_by', 'reviewed_at', 'updated_at',
        ))
        action = (
            auditlog.AuditLog.Action.REQUEST_APPROVED
            if blood_request.status == BloodRequest.Status.APPROVED
            else auditlog.AuditLog.Action.REQUEST_REJECTED
        )
        auditlog.record(
            action,
            entity_type="bloodrequest",
            entity_id=blood_request.tracking_id,
            actor=request.user,
            new_value=blood_request.status,
            reason=blood_request.review_note,
        )
        messages.success(request, f'Request {blood_request.tracking_id} was updated.')
    elif blood_request.status != BloodRequest.Status.PENDING:
        messages.warning(request, 'This request has already been reviewed.')
    else:
        messages.error(request, 'Choose a valid review action and complete the form.')
    return redirect('requests:queue')


@user_passes_test(is_staff)
def issue_blood(request, tracking_id):
    """
    Issue approved-request blood from the unified inventory source of truth
    (Part 2.A / Part 3.E). Decrements inventory.BloodInventory batches via
    inventory.services.issue_units, which is itself atomic and
    select_for_update-locked -- this view's own transaction.atomic() wraps
    both that call and the request/BloodIssue writes so the whole operation
    (inventory decrement, issue record, request status) commits or fails
    together.
    """
    if request.method != 'POST':
        return redirect('requests:queue')

    blood_request = get_object_or_404(BloodRequest, tracking_id=tracking_id)
    form = IssueForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Enter a valid issue note.')
        return redirect('requests:queue')

    with transaction.atomic():
        blood_request = BloodRequest.objects.select_for_update().get(pk=blood_request.pk)
        if blood_request.status != BloodRequest.Status.APPROVED:
            messages.error(request, 'Only approved requests can be issued.')
            return redirect('requests:queue')
        if BloodIssue.objects.filter(request=blood_request).exists():
            # request.models.BloodIssue.request is OneToOneField(unique), so
            # this can't double-fire in practice, but failing with a clear
            # message here (Part 3.E "prevention of duplicate issues")
            # avoids relying solely on an IntegrityError bubbling up.
            messages.error(request, 'This request has already been issued against.')
            return redirect('requests:queue')

        try:
            issue_units(
                blood_group=blood_request.blood_group,
                quantity=blood_request.quantity,
                performed_by=request.user,
                reason=f"Issued against request {blood_request.tracking_id}",
            )
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
            return redirect('requests:queue')

        blood_issue = BloodIssue.objects.create(
            request=blood_request,
            blood_group=blood_request.blood_group,
            quantity=blood_request.quantity,
            issued_by=request.user,
            issue_note=form.cleaned_data['issue_note'],
        )
        blood_request.status = BloodRequest.Status.FULFILLED
        blood_request.save(update_fields=('status', 'updated_at'))
        auditlog.record(
            auditlog.AuditLog.Action.BLOOD_ISSUED,
            entity_type="bloodrequest",
            entity_id=blood_request.tracking_id,
            actor=request.user,
            new_value=f"{blood_issue.quantity}u {blood_issue.blood_group}",
        )

    messages.success(request, f'{blood_request.quantity} unit(s) issued successfully.')
    return redirect('requests:queue')
