import datetime
from datetime import date

from django.contrib.auth import logout
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect

from apps.financials.forms import FeesPackageForm, FeesPackageDetailsForm, FinancialTransactionsForm, InvoiceForm
from apps.financials.models import FeesPackage, FeesPackageDetails, FinancialTransactions, Invoice
from django.http import HttpResponse, JsonResponse

# Create your views here.
from apps.settings.models import AcademicSessions, AcademicTimeLine, ClassRooms, AcademicCalender
from apps.students.forms import EnrollmentForm
from apps.students.models import Enrollments, Students
# from apps.students.views import financial_transactions
from apps.utils import get_school_id


def financial_package_list(request, *args, **kwargs):
    context = {}
    sch_id = get_school_id(request)

    packages = FeesPackage.objects.filter(status='Active', school__sch_id=sch_id)
    # print(str(packages.query)) # print the SQL query to terminal
    context = {'packages': packages}
    return render(request, 'financial/schoolfees-package-list.html', context)


def fee_package_details(request, pkg, mode):
    x = 0
    for i in request.POST.getlist('item_descx'):
        pd_form = FeesPackageDetailsForm(request.POST)

        if pd_form.is_valid():
            # --------  PACKAGE-DETAILS FORM  ------------ '
            pd = pd_form.save(commit=False)

            pd.package_id = pkg.pk
            pd.item_descx = request.POST.getlist('item_descx')[x]
            pd.qty = request.POST.getlist('qty')[x]
            pd.unit_value = request.POST.getlist('unit_value')[x]
            pd.amount = request.POST.getlist('amount')[x]
            pd.save()
            x = x + 1

            status = 'pass'
            if mode == 'update':
                response = {'msg': 'The Fee Package is UPDATED successfully', 'oprx': status}  # response message
            else:
                response = {'msg': 'The Fee Package is SAVED successfully', 'oprx': status}  # response message
        else:
            status = 'fail'
            response = {'msg': 'The Fee Package Details failed to SAVE or UPDATED.', 'oprx': status}  # response message
    return response


def new_package(request, *args, **kwargs):
    # Save new package and return json data
    sch_id = get_school_id(request)

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if is_ajax:
            pkg = 0
            status = 'fail'
            response = {}

            pkg_form = FeesPackageForm(request.POST)
            if pkg_form.is_valid():
                try:
                    pkg = pkg_form.save()
                except:
                    response = {'msg': 'The Fee Package is NOT SAVED. Something is not right', 'oprx': status}
            else:
                response = {'msg': 'The Fee Package is NOT SAVED. You may have enter the same Package before.', 'oprx': status}

            if pkg:
                response = fee_package_details(request, pkg, 'new')

            return JsonResponse(response, safe=False)  # return response as JSON

        else:
            return redirect(financial_package_list)

    else:
        # return HttpResponse('New Fees Package')
        timeline = 1
        package = {'sch_id': sch_id, 'timeline': timeline, 'mode': 'NEW'}
        context = {'package': package}
        return render(request, 'financial/new-package.html', context )


def delete_package(request, pkg_id):
    sch_id = get_school_id(request)
    try:
        package = FeesPackage.objects.get(id=pkg_id, school__sch_id=sch_id)
        if package:
            package.delete()
            messages.success(request, 'The selected Fee Package is successfully deleted.')

    except FeesPackage.DoesNotExist:
        messages.warning(request, 'The Fee Package does not exist. Delete Operation failed')
    except Exception as e:
        raise e
        messages.error(request, 'The Delete Operation failed. Something went wrong')

    return redirect(financial_package_list)


def edit_package(request, pkg_id):

    sch_id = get_school_id(request)

    if request.method == 'POST':
        pkg = FeesPackage.objects.get(id=pkg_id)
        pkg_form = FeesPackageForm(request.POST, instance=pkg)

        if pkg_form.is_valid():
            pkg = pkg_form.save()

            if pkg:
                pkgdet = FeesPackageDetails.objects.filter(package=pkg.id, school=sch_id).delete() # Delete Package details
                response = fee_package_details(request, pkg, 'update')
        else:
            status = 'Failed'
            response = {'msg': 'The Fee Package is NOT SAVED. You may have enter the same Package before.', 'oprx': status}

        return JsonResponse(response, safe=False)  # return response as JSON

    else:
        package = FeesPackage.objects.get(id=pkg_id, school__sch_id=sch_id)

        timeline = 1
        packages = {'sch_id': sch_id, 'timeline': timeline, 'mode': 'UPDATE', 'main': package}
        context = {'package': packages}

        return render(request, 'financial/new-package.html', context )


@transaction.atomic()
def new_student_enrollment(request, reg_id):
    context = {}

    sch_id = get_school_id(request)

    if request.method == 'POST':
        enrollment = EnrollmentForm(request.POST or None)
        status = 'Enrolled'
        if enrollment.is_valid():
            enrolled = enrollment.save(commit=False)
            enrolled.status = status
            enrolled.save()
            # print(enrolled.id)
            inv_no = request.POST['invoice_no']

            financial_transactions(request, 'save', enrolled.id, inv_no)
            # Update Student Status to Enrolled
            stud = Students.objects.filter(id=reg_id).update(reg_status=status, reg_steps=3)

            context = {"enrolled": enrolled}
        else:
            messages.info(request, enrollment.errors)
            messages.warning(request, 'Form did not saved')
            return redirect(new_student_enrollment, reg_id=reg_id)

        if request.POST.get("save_and_list"):
            return redirect('list-enrollments')

        elif request.POST.get("save_and_add"):
            return redirect("new_registeration")
        else:
            # return redirect('/index.html') # Directs to home page -- working
            return redirect('home')

    else:
        context = {}

        student = Students.objects.get(id=reg_id)
        # timeline = AcademicTimeLine.objects.values('id', 'sch_id', 'descx', 'status').get(status='active',sch_id=sch_id)
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id, pkg_type__icontains='new')
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id, status='Active').order_by('term_id')

        context = {
            'student': student, 'timeline': timeline, 'classes': classes, 'fees': fees, 'sessions': sessions
        }
        return render(request, 'financial/reg-enrollment.html', context)


@transaction.atomic
def cancel_enrollment(request, enr_id, inv_no):
    sch_id = get_school_id(request)
    print(f'==== = Sch_ID: {sch_id} Cancelling Enrollment ID: {enr_id} and Invoice No: {inv_no} =  =====')

    inv = Invoice.objects.filter(school=sch_id, enrolled=enr_id, invoice_no=inv_no).first()
    stud_id = inv.student_id
    trans = FinancialTransactions.objects.filter(school=sch_id, enrolled=enr_id, invoice_no=inv_no).first()
    enrlmt = Enrollments.objects.filter(school=sch_id, id=enr_id, status='Enrolled').first()

    todays_dt = date.today()
    if todays_dt.isoformat() <= inv.trans_date.isoformat():
        print(f'Todays Date: {todays_dt}, Invoice Date:  {inv.trans_date}')

        try:
            update = Students.objects.filter(school=sch_id, id=stud_id).update(reg_steps=2, reg_status='pending')
            if update:
                inv.delete()
                trans.delete()
                enrlmt.delete()

        except:
            messages.error(request, 'The operation was not successful. ')
        finally:
            messages.success(request, 'The Student Enrollment is Cancelled.  You may want to Enroll the candidate again')

        print(
            f'Delete Transactions: \n {trans} \n {inv} \n {enrlmt} \n Student ID: {stud_id} \n Student Update: {update}')
    else:
        print('Date not Match: ')
        messages.info(request, 'The action carried was NOT successful.  Cancellation can be done only on the date of enrollment')

    return redirect('list-enrollments')


@transaction.atomic
def update_enrollment(request, enr_id, inv_no):
    sch_id = get_school_id(request)

    if request.method == 'POST':
        enrolled = Enrollments.objects.get(school=sch_id, id=enr_id)
        enrlmt_frm = EnrollmentForm(request.POST, instance=enrolled)

        if enrlmt_frm.is_valid():
            status = 'Enrolled'
            enrolled = enrlmt_frm.save(commit=False)
            enrolled.status = status
            enrolled.save()

            financial_transactions(request, 'update', enrolled.id, inv_no)
            # Update Student Status to Enrolled
            reg_id = request.POST['student']
            stud = Students.objects.filter(id=reg_id).update(reg_status=status, reg_steps=3)

            context = {"enrolled": enrolled}
            messages.success(request, 'Student Enrolled Updated')
        else:
            messages.info(request, enrlmt_frm.errors)
            messages.warning(request, 'Form did not saved')
            return redirect(update_enrollment, enr_id=enr_id, inv_no=inv_no)

        if request.POST.get("save_and_list"):
            return redirect('list-enrollments')

        elif request.POST.get("save_and_add"):
            return redirect("new_registeration")
        else:
            # return redirect('/index.html') # Directs to home page -- working
            return redirect('home')

    else:
        header = 'Edit Student Enrolled'
        enrolled = Enrollments.objects.filter(school=sch_id, id=enr_id).first()
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id, status='Active').order_by('term_id')
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id, pkg_type__icontains='new')
        invoice = Invoice.objects.get(school=sch_id, invoice_no=inv_no)

        context = {'header': header, 'enrolled': enrolled, 'sessions': sessions, 'timeline': timeline, 'classes': classes, 'fees': fees, 'inv': invoice}
        return render(request, 'financial/edit-student-enrolled.html', context)



def financial_transactions(request, action, enr_id, inv_no):
    sch_id = get_school_id(request)

    # with transaction.set_autocommit():
    # -- Save / Update Financial Transactions
    if action == 'update':
        f_trans = FinancialTransactions.objects.get(school=sch_id, invoice_no=inv_no)
        trans_form = FinancialTransactionsForm(request.POST, instance=f_trans)
    else:
        trans_form = FinancialTransactionsForm(request.POST or None)
    if trans_form.is_valid():
        trans = trans_form.save(commit=False)
        trans.enrolled_id = enr_id
        trans.tr_type = 'Dr'
        trans.save()

    #  --- Save / Update Invoice
    if action == 'update':
        invoice = Invoice.objects.get(school=sch_id, invoice_no=inv_no)
        invoice_form = InvoiceForm(request.POST or None, instance=invoice)
    else:
        invoice_form = InvoiceForm(request.POST or None)
    if invoice_form.is_valid():
        inv = invoice_form.save(commit=False)
        inv.due_date = ap_due_date(request)
        inv.enrolled_id = enr_id
        inv.package_id = request.POST['fee_pkg']
        inv.status = 'np'
        inv.save()

    return None


def ap_due_date(request):
    date_now = datetime.date.today()

    sch_id = request.POST['school']
    timeline = request.POST['timeline']
    session_id = request.POST['session']

    term = AcademicSessions.objects.values('term_id').filter(id=session_id, status='Active', sch_id= sch_id).first()  # filter returns queryset
    if term:
        # print('Term: ', term['term_id'])
        term_id = term['term_id']

        date = AcademicCalender.objects.values('cs_start_dt').filter(school=sch_id, tl_id=timeline, term_id=term_id)[0]
        if date:
            due_date = date['cs_start_dt']
            if date_now > due_date:
                due_date = date_now
        # print(sch_id, timeline, term['term_id'], due_date)
        else:
            due_date = date_now
    else:
        due_date = date_now

    return due_date


def list_enrollments(request):
    sch_id = get_school_id(request)
    context = {}

    students_enrolled = Invoice.objects.filter(school=sch_id, enrolled__status='Enrolled').select_related('student', 'enrolled')

    context = {'enrollments': students_enrolled}
    return render(request, 'financial/student-enrolled-list.html', context)