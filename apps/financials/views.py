import datetime
from datetime import date

from django.contrib.auth import logout
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect

from apps.financials.forms import *
from apps.financials.models import FeesPackage, FeesPackageDetails, FinancialTransactions, Invoice, PaymentMethods, Banks
from django.http import HttpResponse, JsonResponse

from apps.settings.models import AcademicSessions, AcademicTimeLine, ClassRooms, AcademicCalender
from apps.students.forms import EnrollmentForm
from apps.students.models import Enrollments, Students
from apps.utils import schools, get_cur_session
from django.db.models import Sum, Q, F


# Create your views here.
def financial_package_list(request, *args, **kwargs):
    context = {}
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

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
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

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
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

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
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

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
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    if request.method == 'POST':

        status = 'enrolled'
        inv_no = request.POST['invoice_no']

        enrollment = EnrollmentForm(request.POST or None)
        if enrollment.is_valid():
            enrolled = enrollment.save(commit=False)
            enrolled.first_inv_no = inv_no
            enrolled.status = status
            enrolled.save()
            # print(enrolled.id)
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
        return render(request, 'financial/student-enrollment.html', context)


@transaction.atomic
def cancel_enrollment(request, enr_id, inv_no):
    sch_id = schools(request)['sch_id']
    # print(f'==== = Sch_ID: {sch_id} Cancelling Enrollment ID: {enr_id} and Invoice No: {inv_no} =  =====') , inv_no

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
def student_enrolled_update(request, enr_id, inv_no):
    sch_id = schools(request)['sch_id']

    if request.method == 'POST':
        enrolled = Enrollments.objects.get(school=sch_id, id=enr_id)
        enrlmt_frm = EnrollmentForm(request.POST, instance=enrolled)

        if enrlmt_frm.is_valid():
            status = 'enrolled'
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
            return redirect(student_enrolled_update, enr_id=enr_id, inv_no=inv_no)

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


def student_re_enrollment(request, stud_id):
    sch_id = schools(request)['sch_id']

    if request.method == 'POST':

        status = 'returned'
        inv_no = request.POST['invoice_no']

        enrollment = EnrollmentForm(request.POST or None)
        if enrollment.is_valid():
            enrolled = enrollment.save(commit=False)
            enrolled.first_inv_no = inv_no
            enrolled.status = status
            enrolled.save()
            # print(enrolled.id)
            financial_transactions(request, 'save', enrolled.id, inv_no)
            # Update Student Status to Enrolled
            stud = Students.objects.filter(id=stud_id).update(reg_status='enrolled', reg_steps=3)
            updated = Enrollments.objects.filter(status='active', school_id=sch_id, student_id=stud_id).update(status='closed')

            context = {"enrolled": enrolled}
        else:
            messages.info(request, enrollment.errors)
            messages.warning(request, 'Form Validation Failed')
            return redirect(student_re_enrollment, stud_id=stud_id)

        if request.POST.get("save_and_list"):
            return redirect('list-enrollments')

        elif request.POST.get("save_and_add"):
            return redirect("new_registeration")
        else:
            return redirect('home')
    else:

        header = 'Student Re-Enrollment'
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        enrolled = Enrollments.objects.filter(school=sch_id, student_id=stud_id).first()
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id, status='Active').order_by('term_id')
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id, pkg_type__icontains='returning')

        context = {'header': header, 'timeline': timeline,'enrolled': enrolled,
                   'sessions': sessions, 'classes': classes, 'fees': fees, 'stud_id': stud_id}
        return render(request, 'financial/student-re-enrollment.html', context)
        # return HttpResponse(f'Student Re-Enrollment: ID-No:- {stud_id}')

def financial_transactions(request, action, enr_id, inv_no):
    sch_id = schools(request)['sch_id']

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
        inv.balance = inv.amount
        inv.enrolled_id = enr_id
        inv.package_id = request.POST['fee_pkg']
        inv.status = 'np'
        inv.save()

    return None


def ap_due_date(request):
    date_now = datetime.date.today()

    sch_id = request.POST['school']['sch_id']
    timeline = request.POST['timeline']
    session_id = request.POST['session']

    term = AcademicSessions.objects.values('term_id').filter(id=session_id, status='Active', sch_id= sch_id).first()  # filter returns queryset
    if term:
        # print('Term: ', term['term_id'])
        term_id = term['term_id']

        date = AcademicCalender.objects.values('cs_start_dt').filter(school=sch_id, timeline=timeline, term_id=term_id)[0]
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
    sch_id = schools(request)['sch_id']

    if sch_id == 0:
        return redirect("logout")

    context = {}

    # students_enrolled = Invoice.objects.filter(school=sch_id, enrolled__status='Enrolled').select_related('student', 'enrolled')
    criteria1 = (Q(status='enrolled') | Q(status = 'active') | Q(status = 'returned')) & Q(school_id=sch_id)
    students_enrolled = Enrollments.objects.filter(criteria1).order_by('school_id', 'classroom_id', 'student__surname')
    # print(students_enrolled)

    context = {'enrollments': students_enrolled}
    return render(request, 'financial/student-enrolled-list.html', context)


@transaction.atomic
def student_payment(request, stud_id):
    sch_id = schools(request)['sch_id']
    enrolled = Enrollments.objects.filter(school=sch_id, student_id=stud_id).order_by('id').last()
    # enrolled = Enrollments.objects.filter(school=sch_id, id=enr_id).first()
    # stud_id = enrolled.student_id
    enr_id = enrolled.id

    qc1 = Q(student_id=stud_id) & Q(school_id=sch_id) & (Q(status='np') | Q(status='pp'))
    inv = Invoice.objects.values('invoice_no', 'descx', 'amount', 'balance').filter(qc1).order_by('invoice_no')

    if request.method == 'POST':
        amt_paying = float(request.POST['amt_paid'])

        recpt_no = generate_receipt_no()
        cur_sesx_id = get_cur_session(sch_id)
        #print(cur_session)

        for i in inv:
            if amt_paying <= 0:
                break
            else:
                p_inv = process_invoice(amt_paying, i, sch_id, stud_id)
                amt_paying = p_inv['pay_bal']

            inv_no = p_inv['invoice_no']
            inv_bal = p_inv['inv_bal']
            status = p_inv['status']

            payment = PaymentForm(request.POST or None)
            if payment.is_valid():
                pmt = payment.save(commit=False)

                pmt.session_id = cur_sesx_id['sesx_id']
                pmt.invoice_no = inv_no
                pmt.receipt_no = recpt_no
                pmt.status = status
                pmt.pmt_descx = p_inv['descx']
                pmt.amt_paid = p_inv['amt_paid']
                pmt.save()

                update = Invoice.objects.filter(school=sch_id, invoice_no=inv_no).update(balance=inv_bal, status=status)
                Enrollments.objects.filter(school=sch_id, id=enr_id).update(last_rcpt_no=recpt_no, status='active')
                print('Form process is Successful.')
            else:
                print('Error with Form process.')

        return redirect(list_enrollments)

    else:
        header = 'Payment'
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        paymethod = PaymentMethods.objects.all()
        bank = Banks.objects.filter(status='active')
        '''
         Query Child object (Invoice) through Parent object (Enviroments)with selected columns
        inv_descx = Enrollments.objects.values('invoice__descx').distinct().filter(qc1).order_by('invoice__invoice_no')
        
        '''
        pay_descx = ''
        for i in inv:
            # print (i['descx'])
            pay_descx = pay_descx + i['descx'] + '; \n'

        context = {'header': header, 'enrolled': enrolled, 'timeline': timeline, 'paymethods': paymethod, 'banks': bank,
                   'descx': pay_descx}
        return render(request, 'financial/student-payment.html', context)


def process_invoice(amt_paying, inv, sch_id, stud_id):
    """ Function is use to get or Generate the following:
        Invoice No: Gotten from the form that POST it
        Invoice Balance: Balance after payment for the specifed invoice
                The balance is written on the column of the Invoice Table
        Amount Paid: Calculate the amount that is paid for the Invoice
        Status: Genrate Either Paid Full (pf) or Part payment (pp)
        Paying_Bal: The amount remaining for next invoice if payment is for more than one invoice
        Payment Description: Generate Description for receipt
    """
    inv_no = inv['invoice_no']
    inv_bal = float(inv['balance'])
    inv_descx = inv['descx']

    if amt_paying >= inv_bal:
        amt_paid = inv_bal
        inv_bal = 0
        amt_paying = amt_paying - amt_paid
    else:
        amt_paid = amt_paying
        inv_bal = inv_bal - amt_paid
        amt_paying = 0

    if inv_bal > 0 and amt_paid > 0:
        status = 'pp'
        inv_descx = 'Part Payment: - ' + inv_descx
    elif inv_bal <= 0:
        # Generate Payment Description by Concatenating string and also set payment status to either Full Payment or Partial payment
        status = 'pf'
        pay_count = Payments.objects.filter(invoice_no=inv_no, school_id=sch_id, student_id=stud_id).count()
        if pay_count == 0:
            inv_descx = 'Full Payment: - ' + inv_descx
        else:
            inv_descx = 'Balance Payment: - ' + inv_descx

    result = {'invoice_no': inv_no, 'inv_bal': inv_bal, 'amt_paid': amt_paid, 'status': status,
              'pay_bal': amt_paying, 'descx': inv_descx}
    return result


def generate_receipt_no():
    p = Payments.objects.values('receipt_no').order_by('school_id', 'id').last()
    if p is None:
        recpt_no = 1
    else:
        recpt_no = int(p['receipt_no']) + 1

    return recpt_no


