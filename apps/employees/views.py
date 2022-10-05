from django.http import HttpResponse
from django.shortcuts import render, redirect
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
    if req.method == 'POST':
        pass
    else:
        return render(req, 'employee-form.html')


def employee_update(req, emp_id=0):
    if emp_id == 0:
        return HttpResponse('Employee for Update is not given . . . ')
    else:
        return HttpResponse('Employee Updated . . . ')

    return render(req, 'employee-form.html')