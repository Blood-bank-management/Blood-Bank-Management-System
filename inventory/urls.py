from django.urls import path
from .views import availability_search

urlpatterns = [
    path("availability/", availability_search, name="availability_search"),
]