
from django.urls import path
from . import views

urlpatterns = [
    path(
        "availability/",
        views.availability_search,
        name="availability_search",
    ),
    path(
        "inventory-summary/",
        views.inventory_summary,
        name="inventory_summary",
    ),
    path(
        "expired-units/",
        views.expired_units,
        name="expired_units",
    ),
]
