import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from apps.decorators import custom_permission_required
from apps.employees.forms import EmployeeForm, NextofkinForm, UserForm, UserFormUpdate
from apps.employees.models import Employees, Departments, Workgroup, Nextofkin
from apps.settings.models import SchoolProfiles
from apps.utils import schools


@login_required
@permission_required("employees.view_employees", login_url="logout")
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
                staff_no = Employees.objects.exclude(staff_no__isnull=True, school=sch_id).order_by(
                    'staff_no').last().staff_no
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


def nextofkin(action, req, sch_id, emp):
    print('Function: save_nextofking')

    if req.POST.get('surname_k') != '' or req.POST.get('other_names_k') != '':
        # if emp.has_nextkin == "Yes":
        if action == 'save':
            kin_form = NextofkinForm(req.POST or None)
            if kin_form.is_valid():
                print('----- Next of Kin Form is Valid')
                kin = kin_form.save(commit=False)
                kin.school_id = sch_id
                kin.employee_id = emp.id
                kin.save()
            else:
                messages.warning(req, kin_form.errors)

        elif action == 'update':
            kin = Nextofkin.objects.get(school_id=sch_id, employee_id=emp.id)
            kin_form = NextofkinForm(req.POST or None, instance=kin)
            if kin_form.is_valid():
                try:
                    kin = kin_form.save(commit=False)
                    kin.school_id = sch_id
                    kin.save()

                except IntegrityError as e:
                    err_msg = getattr(e, 'message', repr(e))
                    messages.error(req, err_msg)
            else:
                messages.warning(req, kin_form.errors)
    else:
        messages.info(req, 'Next of Kin is NOT Saved or Updated')


def user(action, req, sch_id, emp):
    print('Function: user')
    if action == 'save' and req.POST.get('is_active'):
        user_form = UserForm(req.POST or None)
        if user_form.is_valid():
            print('----- User Form is valid')
            user = user_form.save(commit=False)
            user.username = req.POST['username'].lower()
            user.password = make_password(req.POST['password'].lower())
            is_superuser = req.POST.get('is_superuser')
            user.save()

            # Update user_id column in Employees model to the new user_id created
            emp.user_id = user.id
            emp.save()
        else:
            print('----- User Form is NOT valid')
            messages.warning(req, user_form.errors)

    elif action == 'update':
        print('----- User Update: ' + emp.staff_no)
        if emp.user_id:
            print('----- User ID: ' + str(emp.user_id))
            user = User.objects.get(id=emp.user_id)
            user_form = UserFormUpdate(req.POST or None, instance=emp.user)
            if user_form.is_valid():
                print('----- User Form is Valid for Update')
                user_form.save()
            else:
                print('----- Form is NOT valid for Update')
        else:
            print('----- Creating New User')
            user_form = UserForm(req.POST or None)
            if user_form.is_valid():
                print('----- New User Form is Valid')
                user = user_form.save(commit=False)
                user.username = req.POST['username'].lower()
                user.password = make_password(req.POST['password'].lower())
                user.save()

                # Update user_id column in Employees model to the new user_id created
                emp.user_id = user.id
                emp.save()
            else:
                print('----- New User Form is NOT Valid')


@login_required
@custom_permission_required("employees.add_employees")
@transaction.atomic()
def new_employee_entry(req):
    """ New Employee Entry"""
    print('new_employee_entry :  -------------')

    school = schools(req)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    emp_id = 0
    header = 'Employee Entry'
    emp_posix = Group.objects.filter(workgroup__school_id=sch_id).order_by('id')  # Get Position List ( or Group list)
    emp_dept = Departments.objects.filter(school=sch_id).order_by('id')  # Get Departments list

    if req.method == 'POST':
        print('---- Posting Form')
        emp_form = EmployeeForm(req.POST or None)

        if emp_form.is_valid():
            print('----- Form is Valid')
            emp = emp_form.save(commit=False)
            emp.staff_no = req.POST['staff_no']
            emp.school_id = sch_id
            if req.FILES:
                emp.emp_pic = req.FILES['emp_pic']


            try:
                emp.save()
                # if req.POST.get('surname_k') != '':
                nextofkin('save', req, sch_id, emp)
                user('save', req, sch_id, emp)  # Update

            except IntegrityError as e:
                err_msg = getattr(e, 'message', repr(e))
                print(err_msg)
                messages.error(req, err_msg)
                context = {'header': header, 'emp_id': emp_id, 'emp': req.POST}

                return render(req, 'employee-form.html', context)

            messages.success(req, 'New Employee entry Saved successfully.')
            return redirect("list-employees")
        else:
            # if the form processed is having in-Valid data
            messages.error(req, emp_form.errors)
            context = {'header': header, 'emp_id': emp_id, 'emp': req.POST, 'positions': emp_posix,
                       'departments': emp_dept}
            return render(req, 'employee-form.html', context)
    else:
        staff_no = new_staff_no(sch_id)
        next_staff_no = {'staff_no': staff_no}
        print('----- GET Operation: Blank Form for New Entry')
        print(next_staff_no)
        context = {'header': header, 'emp_id': emp_id, 'positions': emp_posix, 'departments': emp_dept,
                   'emp': next_staff_no}

        return render(req, 'employee-form.html', context)


@custom_permission_required("employees.change_employees")
@transaction.atomic()
def employee_update(req, emp_id=0):
    """ Function to Update Employee Details:"""

    school = schools(req)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    header = 'Employee Update'
    try:
        employee = Employees.objects.get(id=emp_id, school=sch_id)
        try:
            next_kin = Nextofkin.objects.get(school=sch_id, employee=employee)  # Query for next of kin
        except Nextofkin.DoesNotExist:
            next_kin = {}  # if nextofkin does not exist set next_kin to empty dictionary object
    except:
        employee = 0
        messages.warning(req, 'The Employee record you searched for does not exist.  You have being re-directed to Employee list.  ')
        return redirect('list-employees')

    emp_dept = Departments.objects.filter(school=sch_id).order_by('id')  # Get department list
    emp_posix = Group.objects.filter(workgroup__school_id=sch_id).order_by('id')  # Get Position list (or Group list)

    if req.method == 'POST':
        emp_id = req.POST['id']
        if emp_id == 0:
            return HttpResponse('Employee for Update is not given . . . ')
        else:
            # employee = Employees.objects.get(id=emp_id, school=sch_id)
            form = EmployeeForm(req.POST or None, instance=employee)
            # checkboxval = req.POST.get('is_user')
            # print('----- Check Box Value:')
            # print(checkboxval)
            if form.is_valid():
                emp = form.save(commit=False)
                if req.FILES:
                    if len(emp.emp_pic) > 0 and emp.emp_pic != 'images/static/default.png':
                        os.remove(emp.emp_pic.path)
                    emp.emp_pic = req.FILES['emp_pic']
                else:
                    if req.POST.get('emp_pic_default'):
                        os.remove(emp.emp_pic.path)
                        emp.emp_pic = req.POST["emp_pic_default"]
                        # print('Employee Pic Updated to Default')

                emp.save()

                msg1 = ''
                if next_kin:  # If successful query of next of kin,
                    nextofkin('update', req, sch_id, emp)  # Update
                    msg1 = ' and Next of Kin'
                else:
                    #  if next of kin is entered
                    if req.POST.get('surname_k') != '' and req.POST.get('other_names_k') != '':
                        nextofkin('save', req, sch_id, emp)  # create a new next of kin record
                        msg1 = ' and Next of Kin'

                user('update', req, sch_id, emp)  # Update

                msg = 'Employee ' + msg1 + ' Updated successfully.'
                messages.success(req, msg)
                print('---- Employee Form is Valid. And Updated')
                return redirect('list-employees')
            else:
                print('----- Employee form is NOT Valid ')
                # messages.error(req, 'Employee NOT Updated: There is an Invalid Form Entry.')
                messages.error(req, form.errors)

                context = {'header': header, 'emp_id': emp_id, 'emp': employee, 'positions': emp_posix,
                           'departments': emp_dept, 'kin': next_kin}
                return render(req, 'employee-form.html', context)
    else:
        context = {'header': header, 'emp_id': emp_id, 'emp': employee, 'positions': emp_posix,
                   'departments': emp_dept}
        return render(req, 'employee-form.html', context)


def modalform_save(request):
    """ Save Modal forms in Employee form. The Modal Forms are Position and Department forms
        The forms will pop up when the Add Position or Add Department of the Select Inputs are Selected """
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
            try:
                g = Group.objects.create(name=posix)  # Insert the new Position
                wg = Workgroup.objects.create(group=g, school_id=sch_id)
                data = {'id': g.id, 'position': posix, 'frm_name': frm, 'error': ''}
                print(f'Group ID: {g.id},  Workgroup ID: {wg.id}')

            except IntegrityError as e:
                err_msg = getattr(e, 'message', repr(e))
                data = {'error': str(err_msg), 'frm_name': frm}

        elif frm == 'department':
            dept = request.POST['new_department']
            print('Department Entered: ' + dept)
            try:
                d = Departments.objects.create(school_id=sch_id, name=dept)
                print(f'Department ID: {d.id},  Name: {d.name} frm_name: {frm} ')
                data = {'id': d.id, 'department': dept, 'frm_name': frm, 'error': ''}

            except IntegrityError as e:
                err_msg = getattr(e, 'message', repr(e))
                data = {'error': str(err_msg), 'frm_name': frm}

    return JsonResponse({'data': data})
