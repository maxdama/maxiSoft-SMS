from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect

from apps.employees.forms import EmployeeForm
from apps.employees.models import Employees
from apps.utils import schools


def list_employees(request):
    """
    List Employees base on the supplied criteria
    """
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    employees = Employees.objects.filter(school=sch_id)
    print(employees)
    context = {'employees': employees}
    return render(request, 'employees-list.html', context)


def employee_entry(req):
    """ New Employee Entry"""
    print('employee_entry :- Function')
    emp_id = 0
    if req.method == 'POST':
        print('---- Posting Form')
        employee = EmployeeForm(req.POST or None)
        if employee.is_valid():
            print('----- Form is Valid')
            emp = employee.save(commit=False)
            emp.staff_no = 'NGS-006'

            emp.save()

            messages.info(req, 'New Employee Saved')
            return redirect("list-employees")
    else:
        context = {'header': 'Employee Entry', 'emp_id': emp_id}
        return render(req, 'employee-form.html', context)


def employee_update(req, emp_id=0):
    """ Function to Update Employee Details:"""
    if req.method == 'POST':
        if emp_id == 0:
            return HttpResponse('Employee for Update is not given . . . ')
        else:
            return HttpResponse('Employee Updated . . . ')
    else:
        header = 'Employee Update'
        context = {'header': header, 'emp_id': emp_id}
        return render(req, 'employee-form.html', context)