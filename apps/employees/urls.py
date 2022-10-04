from django.urls import path
from . import views

urlpatterns = [
    path('employee-list', views.list_employees, name='list-employees'),
]