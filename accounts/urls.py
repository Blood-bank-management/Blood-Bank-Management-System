from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # NOTE: deliberately not under "admin/*" -- bloodbank/urls.py mounts
    # Django's own admin site at "admin/", which swallows the whole
    # prefix; anything registered under "admin/users/..." here would be
    # unreachable (the admin site's own URLconf would 404 it first).
    path("administration/users/", views.user_list, name="list"),
    path("administration/users/new/", views.user_create, name="create"),
    path("administration/users/<int:pk>/", views.user_detail, name="detail"),
]
