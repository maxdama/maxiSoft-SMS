from django.urls import path
from . import views

urlpatterns = [
    path('staff-list', views.list_employees, name='list-employees'),
    path('new-entry', views.employee_entry, name='new-employee'),
    path('update-entry/<int:emp_id>', views.employee_update, name='update-employee'),
]