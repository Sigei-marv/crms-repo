from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('activity-log/', views.activity_log_view, name='activity_log'),
]