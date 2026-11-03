from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

import auditlog.models as auditlog
from authentication.decorators import admin_required

from .forms import AdminUserCreateForm, AdminUserUpdateForm, RoleChangeForm, UserSearchForm


def _role_of(user):
    if user.is_superuser:
        return AdminUserCreateForm.ROLE_ADMIN
    if user.is_staff:
        return AdminUserCreateForm.ROLE_STAFF
    return AdminUserCreateForm.ROLE_DONOR


def _active_superuser_count(exclude_pk=None):
    qs = User.objects.filter(is_superuser=True, is_active=True)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.count()


@admin_required
def user_list(request):
    """Administrator-only account list with search/filter/pagination (Part 3.D)."""
    form = UserSearchForm(request.GET or None)
    users = User.objects.all().order_by("username")

    query = ""
    role = ""
    status = ""
    if form.is_valid():
        query = form.cleaned_data.get("q", "")
        role = form.cleaned_data.get("role", "")
        status = form.cleaned_data.get("status", "")

        if query:
            users = users.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
                | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
        if role == AdminUserCreateForm.ROLE_ADMIN:
            users = users.filter(is_superuser=True)
        elif role == AdminUserCreateForm.ROLE_STAFF:
            users = users.filter(is_staff=True, is_superuser=False)
        elif role == AdminUserCreateForm.ROLE_DONOR:
            users = users.filter(is_staff=False, is_superuser=False)
        if status == "active":
            users = users.filter(is_active=True)
        elif status == "inactive":
            users = users.filter(is_active=False)

    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "accounts/user_list.html",
        {"page_obj": page_obj, "form": form},
    )


@admin_required
def user_create(request):
    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            auditlog.record(
                auditlog.AuditLog.Action.USER_CREATED,
                entity_type="user",
                entity_id=user.pk,
                actor=request.user,
                new_value=f"username={user.username}, role={form.cleaned_data['role']}",
            )
            messages.success(request, f"Account '{user.username}' created.")
            return redirect("accounts:detail", pk=user.pk)
    else:
        form = AdminUserCreateForm()
    return render(request, "accounts/user_create.html", {"form": form})


@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    update_form = AdminUserUpdateForm(instance=user)
    role_form = RoleChangeForm(initial={"role": _role_of(user)})

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_details":
            update_form = AdminUserUpdateForm(request.POST, instance=user)
            if update_form.is_valid():
                update_form.save()
                messages.success(request, "Account details updated.")
                return redirect("accounts:detail", pk=pk)

        elif action == "change_role":
            role_form = RoleChangeForm(request.POST)
            if role_form.is_valid():
                new_role = role_form.cleaned_data["role"]
                previous_role = _role_of(user)
                is_demoting_only_superuser = (
                    user.is_superuser
                    and new_role != AdminUserCreateForm.ROLE_ADMIN
                    and _active_superuser_count(exclude_pk=user.pk) == 0
                )
                if is_demoting_only_superuser:
                    messages.error(
                        request,
                        "Cannot change this account's role: it is the last active "
                        "administrator account. Promote another account to "
                        "administrator first.",
                    )
                else:
                    user.is_staff = new_role in (AdminUserCreateForm.ROLE_STAFF, AdminUserCreateForm.ROLE_ADMIN)
                    user.is_superuser = new_role == AdminUserCreateForm.ROLE_ADMIN
                    user.save(update_fields=("is_staff", "is_superuser"))
                    auditlog.record(
                        auditlog.AuditLog.Action.USER_ROLE_CHANGED,
                        entity_type="user",
                        entity_id=user.pk,
                        actor=request.user,
                        previous_value=previous_role,
                        new_value=new_role,
                    )
                    messages.success(request, f"Role changed to {new_role}.")
                return redirect("accounts:detail", pk=pk)

        elif action == "toggle_active":
            if user.is_superuser and user.is_active and _active_superuser_count(exclude_pk=user.pk) == 0:
                messages.error(
                    request,
                    "Cannot deactivate this account: it is the last active "
                    "administrator account.",
                )
            else:
                previous = user.is_active
                user.is_active = not user.is_active
                user.save(update_fields=("is_active",))
                auditlog.record(
                    auditlog.AuditLog.Action.USER_ACTIVATION_CHANGED,
                    entity_type="user",
                    entity_id=user.pk,
                    actor=request.user,
                    previous_value=str(previous),
                    new_value=str(user.is_active),
                )
                messages.success(
                    request, f"Account {'activated' if user.is_active else 'deactivated'}.",
                )
            return redirect("accounts:detail", pk=pk)

    return render(
        request,
        "accounts/user_detail.html",
        {"target_user": user, "update_form": update_form, "role_form": role_form, "current_role": _role_of(user)},
    )
