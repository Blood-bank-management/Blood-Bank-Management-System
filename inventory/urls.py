from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.home, name="home"),
    path("availability/", views.availability_search, name="availability_search"),
    path("inventory-summary/", views.inventory_summary, name="inventory_summary"),
    path("staff/batches/", views.batch_list, name="batch_list"),
    path("staff/batches/<int:pk>/", views.batch_detail, name="batch_detail"),
    path("expired-units/", views.expired_units, name="expired_units"),
]
