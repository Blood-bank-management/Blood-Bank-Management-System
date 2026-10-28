from django.urls import path

from . import views

app_name = "donors"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("staff/donors/", views.donor_list, name="list"),
    path("staff/donors/<int:pk>/", views.donor_detail, name="detail"),
]
