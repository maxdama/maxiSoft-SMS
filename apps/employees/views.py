from django.contrib import messages
from django.contrib.auth.models import Group
from django.db import utils
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from apps.employees.forms import EmployeeForm
from apps.employees.models import Employees, Departments, Workgroup
from apps.settings.models import SchoolProfiles
from apps.utils import schools


def list_employees(request):
    """
    List Employees base on the supplied criteria
    """
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    employees = Employees.objects.filter(school=sch_id).order_by('staff_no')
    context = {'employees': employees}
    return render(request, 'employees-list.html', context)


def new_staff_no(sch_id):
    """Generate next staff_no from the last one in Employments table.
        Initiate a new staff_no for the first Employee entered
    """
    profile = SchoolProfiles.objects.filter(sch_id=sch_id).values('name_abr').last()
    if profile:
        if profile['name_abr'] is not None:
            name_abr = profile['name_abr']
            name_abr = str(name_abr[0:2])  # Get the first two string characters
            # add length of name_abr and Sch_id to get the total length of the string part
            tl = len(name_abr) + len(str(sch_id))
            print('Total Length: ')
            print(tl)

            try:
                # Generate the Next Staff_No in the Employee table sequence
                staff_no = Employees.objects.exclude(staff_no__isnull=True, school=sch_id).order_by('staff_no').last().staff_no
                abr = staff_no[0:tl]  # strip out the Abbreviation and school id part of last staff_no
                num = int(staff_no[tl:])  # Strip out the number part from last staff_no
                num = num + 1
                new_num = str(num).zfill(3)
                staff_no = abr + new_num
                print('New Staff No : ')
                print(staff_no)

            except AttributeError:
                # Generate the first Staff_No
                staff_no = name_abr + str(sch_id)
                staff_no = staff_no + str(1).zfill(3)  # Initialize staff_no to 001 and Concatenate with abbreviation

            return staff_no
    else:
        # Instruct that School Profile and Abbreviation have to entered first
        messages.warning(sch_id, "You school Profile must be entered first before you can do any other entries. "
                                 "Please consult with your Software Admin.")
        return None


def new_employee_entry(req):
    """ New Employee Entry"""
    print('new_employee_entry :  -------------')

    school = schools(req)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    emp_id = 0
    header = 'Employee Entry'
    # Get the list of Positions stored in django Group table for the specific School ID
    emp_posix = Group.objects.filter(workgroup__school_id=sch_id).order_by('id')
    # Get the list of departments from Departments table
    emp_dept = Departments.objects.filter(school=sch_id).order_by('id')

    if req.method == 'POST':
        print('---- Posting Form')
        emp_form = EmployeeForm(req.POST or None)
        if emp_form.is_valid():
            print('----- Form is Valid')
            emp = emp_form.save(commit=False)
            emp.school_id = sch_id
            emp.staff_no = new_staff_no(sch_id)
            try:
                emp.save()

            except utils.IntegrityError:
                print('Integrity Error: A key field was duplicated')
                messages.error(req, 'The Data you entered was NOT SAVED: There is integrity of data in a key field.')
                context = {'header': header, 'emp_id': emp_id, 'emp': req.POST}

                return render(req, 'employee-form.html', context)

            messages.success(req, 'New Employee entry Saved successfully.')
            return redirect("list-employees")
        else:
            # if the form processed is having in-Valid data
            messages.error(req, 'The Data you entered was NOT SAVED: The form data is NOT valid.')
            context = {'header': header, 'emp_id': emp_id, 'emp': req.POST, 'positions': emp_posix,
                       'departments': emp_dept}
            return render(req, 'employee-form.html', context)
    else:
        print('----- GET Operation: Blanc Form for New Entry')
        context = {'header': header, 'emp_id': emp_id, 'positions': emp_posix, 'departments': emp_dept}

        return render(req, 'employee-form.html', context)


def employee_update(req, emp_id=0):
    """ Function to Update Employee Details:"""

    school = schools(req)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    header = 'Employee Update'
    employee = Employees.objects.get(id=emp_id, school=sch_id)
    # Get the list of departments from Departments table
    emp_dept = Departments.objects.filter(school=sch_id).order_by('id')
    # Get the list of Positions stored in django Group table for the specific School ID
    emp_posix = Group.objects.filter(workgroup__school_id=sch_id).order_by('id')

    if req.method == 'POST':
        emp_id = req.POST['id']
        if emp_id == 0:
            return HttpResponse('Employee for Update is not given . . . ')
        else:
            employee = Employees.objects.get(id=emp_id, school=sch_id)
            form = EmployeeForm(req.POST or None, instance=employee)

            if form.is_valid():
                emp = form.save(commit=False)
                emp.staff_no = req.POST['staff_no']
                emp.save()

                messages.success(req, 'Employee Updated successfully.')
                print('---- Employee Form is Valid. And Updated')
                return redirect('list-employees')
            else:
                print('----- Employee form is NOT Valid ')
                messages.error(req, 'Employee NOT Updated: There is an Invalid Form Entry.')

                context = {'header': header, 'emp_id': emp_id, 'emp': employee, 'positions': emp_posix, 'departments': emp_dept}
                return render(req, 'employee-form.html', context)
    else:
        print(emp_posix)
        context = {'header': header, 'emp_id': emp_id, 'emp': employee, 'positions': emp_posix, 'departments': emp_dept}
        return render(req, 'employee-form.html', context)


def modalform_save(request):
    print('Function: -- modalform_save  -- ')

    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    data = {}

    if request.method == 'POST':
        frm = request.POST['frm_name']
        print(sch_id)

        if frm == 'position':
            posix = request.POST['new_position']
            g = Group.objects.create(name=posix)  # Insert the new Position
            wg = Workgroup.objects.create(group=g, school_id=sch_id)

            print(f'Group ID: {g.id},  Workgroup ID: {wg.id}')
            data = {'id': g.id, 'position': posix, 'frm_name': frm}

        elif frm == 'department':
            dept = request.POST['new_department']
            print('Department Entered: ' + dept)
            d = Departments.objects.create(school_id=sch_id, name=dept)
            print(f'Department ID: {d.id},  Name: {d.name}')
            data = {'id': d.id, 'department': dept, 'frm_name': frm}

    return JsonResponse({'data': data})
