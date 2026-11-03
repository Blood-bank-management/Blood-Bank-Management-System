from django.urls import path
from . import views

app_name = "donations"

urlpatterns = [
    path("staff/donations/record/", views.record, name="record"),
    path("staff/donations/", views.donation_list, name="list"),
    path("staff/donations/donor/<int:pk>/", views.donor_donation_history, name="donor_history"),
    path("donations/my-history/", views.my_donation_history, name="my_history"),
]
