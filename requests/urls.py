from django.urls import path

from . import views


app_name = 'requests'

urlpatterns = [
    path('', views.request_create, name='create'),
    path('requests/<uuid:tracking_id>/', views.request_detail, name='detail'),
    path('staff/requests/', views.request_queue, name='queue'),
    path('staff/requests/<uuid:tracking_id>/review/', views.request_review, name='review'),
]