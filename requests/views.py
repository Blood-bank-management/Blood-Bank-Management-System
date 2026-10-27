from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import BloodRequestForm, IssueForm, ReviewForm
from .models import BloodInventory, BloodIssue, BloodRequest


def request_create(request):
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save()
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
    requests = BloodRequest.objects.select_related('reviewed_by', 'issue_transaction')
    return render(request, 'requests/request_queue.html', {'requests': requests})


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
        messages.success(request, f'Request {blood_request.tracking_id} was updated.')
    elif blood_request.status != BloodRequest.Status.PENDING:
        messages.warning(request, 'This request has already been reviewed.')
    else:
        messages.error(request, 'Choose a valid review action and complete the form.')
    return redirect('requests:queue')


@user_passes_test(is_staff)
def issue_blood(request, tracking_id):
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

        inventory = (
            BloodInventory.objects.select_for_update()
            .filter(blood_group=blood_request.blood_group)
            .first()
        )
        if inventory is None:
            messages.error(request, f'No inventory record exists for {blood_request.blood_group}.')
            return redirect('requests:queue')
        if inventory.available_units < blood_request.quantity:
            messages.error(
                request,
                f'Insufficient {blood_request.blood_group} inventory. '
                f'{inventory.available_units} unit(s) available.',
            )
            return redirect('requests:queue')

        inventory.available_units -= blood_request.quantity
        inventory.save(update_fields=('available_units', 'updated_at'))
        BloodIssue.objects.create(
            request=blood_request,
            blood_group=blood_request.blood_group,
            quantity=blood_request.quantity,
            issued_by=request.user,
            issue_note=form.cleaned_data['issue_note'],
        )
        blood_request.status = BloodRequest.Status.FULFILLED
        blood_request.save(update_fields=('status', 'updated_at'))

    messages.success(request, f'{blood_request.quantity} unit(s) issued successfully.')
    return redirect('requests:queue')