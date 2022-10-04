from django.http import HttpResponse
from django.shortcuts import render


def list_employees(request):
    # return HttpResponse('Employees List')
    return render(request, 'employees-list.html')