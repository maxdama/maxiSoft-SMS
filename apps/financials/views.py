import datetime
import os
from time import sleep

import psutil as psutil
from reportlab.pdfgen import canvas

from django.contrib import messages
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect

from apps.financials.forms import *
from apps.financials.models import *
from django.http import JsonResponse, HttpResponse

from apps.settings.models import AcademicSessions, AcademicTimeLine, ClassRooms, AcademicCalender
# from apps.students.forms import EnrollmentForm
from apps.students.models import Students
from apps.utils import schools, get_cur_session, generate_reg_no
from django.db.models import Q


# Create your views here.
from core.settings import CORE_DIR


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
                response = {'msg': 'The Fee Package is NOT SAVED. You may have enter the same Package before.',
                            'oprx': status}

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
        return render(request, 'financial/new-package.html', context)


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
                pkgdet = FeesPackageDetails.objects.filter(package=pkg.id,
                                                           school=sch_id).delete()  # Delete Package details
                response = fee_package_details(request, pkg, 'update')
        else:
            status = 'Failed'
            response = {'msg': 'The Fee Package is NOT SAVED. You may have enter the same Package before.',
                        'oprx': status}

        return JsonResponse(response, safe=False)  # return response as JSON

    else:
        package = FeesPackage.objects.get(id=pkg_id, school__sch_id=sch_id)

        timeline = 1
        packages = {'sch_id': sch_id, 'timeline': timeline, 'mode': 'UPDATE', 'main': package}
        context = {'package': packages}

        return render(request, 'financial/new-package.html', context)


@transaction.atomic()
def new_student_enrollment(request, reg_id):
    context = {}
    sch_id = schools(request)['sch_id']
    # sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    if request.method == 'POST':
        trans_id = create_tranaction(request, desc='enrollment', sch_id=sch_id, stud_id=reg_id)

        status = 'enrolled'
        inv_no = request.POST['invoice_no']

        enrollment = EnrollmentForm(request.POST or None)
        if enrollment.is_valid():
            enrolled = enrollment.save(commit=False)
            enrolled.first_inv_no = inv_no
            enrolled.status = status
            enrolled.transaction_id = trans_id
            enrolled.save()

            financial_transactions(request, 'save', enrolled.id, inv_no, trans_id=trans_id)
            # Update Student Status to enrolled
            stud = Students.objects.filter(id=reg_id).update(reg_status=status, reg_steps=3)

            context = {"enrolled": enrolled}
        else:
            messages.info(request, enrollment.errors)
            messages.warning(request, 'Form did not saved')
            return redirect(new_student_enrollment, reg_id=reg_id)

        if request.POST.get("save_and_list"):
            return redirect('list-enrollments')

        elif request.POST.get("save_and_add"):
            return redirect("new-registeration")
        else:
            # return redirect('/index.html') # Directs to home page -- working
            return redirect('home')

    else:
        context = {}

        student = Students.objects.get(id=reg_id)
        # timeline = AcademicTimeLine.objects.values('id', 'sch_id', 'descx', 'status').get(status='active',sch_id=sch_id)
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id,
                                                                                    pkg_type__icontains='new')
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id,
                                                                                    status='Active').order_by('term_id')

        context = {
            'student': student, 'timeline': timeline, 'classes': classes, 'fees': fees, 'sessions': sessions
        }
        return render(request, 'student-enrollment.html', context)


@transaction.atomic
def cancel_enrollment(request, enr_id, inv_no, trans_id):
    sch_id = schools(request)['sch_id']

    trans = FinancialTransactions.objects.get(school_id=sch_id, transaction=trans_id)
    if trans.descx == 'enrollment':

        for inv in trans.invoice.all():
            break

        stud_id = inv.student_id

        todays_date = date.today()
        if todays_date.isoformat() <= inv.trans_date.isoformat():
            try:
                update = Students.objects.filter(school=sch_id, id=stud_id).update(reg_steps=2, reg_status='pending')
                if update:
                    # Delete FinancialTransactions and also Cascaded related tables:
                    # including, FeesAccounts, Invoice and Enrollments
                    trans.delete()
                    messages.success(request, 'The Student Enrollment is Cancelled.  You may want to Enroll the candidate again')
            except:
                messages.error(request, 'The operation was not successful. ')
        else:
            messages.info(request, 'You cannot cancel this transaction today.  Cancellation can be done only on the date of enrollment')

    return redirect('list-enrollments')


@transaction.atomic
def student_enrolled_update(request, enr_id, inv_no):
    sch_id = schools(request)['sch_id']
    print(f'Enrollment ID: {enr_id}; School ID:  {sch_id}; Invoice No:  {inv_no}')

    if request.method == 'POST':
        enrolled = Enrollments.objects.get(school_id=sch_id, id=enr_id)
        # print(f'Transaction: {enrolled.transaction_id}')
        enrlmt_frm = EnrollmentForm(request.POST, instance=enrolled)
        print(f'Transaction: {enrolled.transaction_id}')
        trans_id = enrolled.transaction_id

        if enrlmt_frm.is_valid():
            status = 'enrolled'
            enrlmt = enrlmt_frm.save(commit=False)
            enrlmt.status = status
            enrlmt.transaction_id = trans_id
            enrlmt.save()

            financial_transactions(request, 'update', enrlmt.id, inv_no)
            # Update Student Status to Enrolled
            reg_id = request.POST['student']
            stud = Students.objects.filter(id=reg_id).update(reg_status=status, reg_steps=3)

            context = {"enrolled": enrlmt}
            messages.success(request, 'Student Enrolled Updated')
        else:
            messages.info(request, enrlmt_frm.errors)
            messages.warning(request, 'Form did not saved')
            return redirect(student_enrolled_update, enr_id=enr_id, inv_no=inv_no)

        if request.POST.get("save_and_list"):
            return redirect('list-enrollments')

        elif request.POST.get("save_and_add"):
            return redirect("new-registeration")
        else:
            # return redirect('/index.html') # Directs to home page -- working
            return redirect('home')

    else:
        header = 'Edit Student Enrolled'
        enrolled = Enrollments.objects.filter(school=sch_id, id=enr_id).first()
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id,
                                                                                    status='Active').order_by('term_id')
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id,
                                                                                    pkg_type__icontains='new')
        invoice = Invoice.objects.get(school=sch_id, invoice_no=inv_no)

        context = {'header': header, 'enrolled': enrolled, 'sessions': sessions, 'timeline': timeline,
                   'classes': classes, 'fees': fees, 'inv': invoice}
        return render(request, 'edit-student-enrolled.html', context)


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

            financial_transactions(request, 'save', enrolled.id, inv_no)
            # Update Student Status to Enrolled
            stud = Students.objects.filter(id=stud_id).update(reg_status='enrolled', reg_steps=3)
            updated = Enrollments.objects.filter(status='active', school_id=sch_id, student_id=stud_id).update(
                status='closed')

            context = {"enrolled": enrolled}
        else:
            messages.info(request, enrollment.errors)
            messages.warning(request, 'Form Validation Failed')
            return redirect(student_re_enrollment, stud_id=stud_id)

        if request.POST.get("save_and_list"):
            return redirect('list-enrollments')

        elif request.POST.get("save_and_add"):
            return redirect("new-registeration")
        else:
            return redirect('home')
    else:

        header = 'Student Re-Enrollment'
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        enrolled = Enrollments.objects.filter(school=sch_id, student_id=stud_id).first()
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id,
                                                                                    status='Active').order_by('term_id')
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id,
                                                                                    pkg_type__icontains='returning')

        context = {'header': header, 'timeline': timeline, 'enrolled': enrolled,
                   'sessions': sessions, 'classes': classes, 'fees': fees, 'stud_id': stud_id}
        return render(request, 'financial/student-re-enrollment.html', context)
        # return HttpResponse(f'Student Re-Enrollment: ID-No:- {stud_id}')


def create_tranaction(request, desc, sch_id, stud_id=0):
    """ Generate next Transaction  number"""
    financial = FinancialTransactions.objects.values('transaction').order_by('school_id', 'transaction').last()
    if financial is None:
        trans_id = 1
    else:
        trans_id = int(financial['transaction']) + 1

    # tr_date = request.POST['trans_date']
    tr_date = date.today()
    print(tr_date)

    FinancialTransactions.objects.create(school_id=sch_id, trans_date=tr_date, transaction=trans_id, descx=desc, student_id=stud_id)

    return trans_id


@transaction.atomic
def cancel_financial_transaction(request, sch_id, trans_id):

    try:
        trans = FinancialTransactions.objects.get(school_id=sch_id, transaction=trans_id)
        if trans:
            descx = trans.descx
            if descx == 'enrollment':
                for tr in trans.enrollment.all():
                    status = tr.status
                    recipt_no = tr.last_rcpt_no
                    stud_id = tr.student_id
                    break

                if recipt_no is None:
                    #  Cancel Enrollment, If no payment has been made for Enrolled Student.
                    updated = Students.objects.filter(school_id=sch_id, id=stud_id).update(reg_steps=2, reg_status='pending')
                    if updated:
                        trans.delete()
                        messages.success(request, 'Student Enrolled Cancelled Successfully.')
                    else:
                        messages.error(request, 'Cancellation of Student Enrolled Failed.')
                    return redirect(list_enrollments)
                else:
                    messages.error(request, 'You cannot Cancel this enrorllment now. Payment has already been made')
                    return redirect(list_enrollments)

            elif descx == 'fee payment':
                stud_id = trans.student_id
                f1 = Q(school_id=sch_id) & Q(student_id=stud_id)

                """ Get the distinct Invoice Nos for the transaction you are cancelling from FeesPayment
                   Get the total discount sum from Invoice with Invoice Nos : using in keyword
               """
                inv_nos = []
                invoices = FeesPayments.objects.filter(f1 & Q(transaction_id=trans_id)).values('invoice_no').distinct()

                for x, inv in enumerate(invoices, start=0):
                    inv_nos.append(inv['invoice_no'])

                tot_disc = Invoice.objects.filter(f1 & Q(invoice_no__in=inv_nos)).aggregate(discount=Sum('discount'))
                print("Discount:")
                print(tot_disc['discount'])
                total_discount = tot_disc['discount']

                trans.delete() # Delete all the corresponding transaction
                print(f'Transaction No: {trans_id} is deleted')
                print('Invoice Nos:')
                print(inv_nos)

                pmt_counts = FeesPayments.objects.filter(f1).count()
                due = FeesAccounts.objects.filter(school_id=sch_id, student_id=stud_id).aggregate(balance=Sum('amount'))
                due_balance = due['balance'] - total_discount
                last = FeesPayments.objects.filter(f1).values('receipt_no').order_by('receipt_no').last()
                print(last)
                if last is None:
                    last = {'receipt_no': None}

                if pmt_counts > 0 and due['balance'] > 0:
                    status = 'paying'
                    status_inv = 'pp'
                elif pmt_counts > 0:
                    status = 'paid'
                    status_inv = 'pf'
                else:
                    status = 'enrolled'
                    status_inv = 'np'
                    Students.objects.filter(school_id=sch_id, id=stud_id).update(reg_status=status)

                enrlmt = Enrollments.objects.filter(f1 & ~Q(status='close'))
                print(enrlmt)
                trans_id_enrlmt = enrlmt[0].transaction_id
                enrlmt.update(status=status, last_rcpt_no=last["receipt_no"])
                print('Enrollment')
                print(enrlmt)

                inv = Invoice.objects.filter(f1 & Q(transaction_id=trans_id_enrlmt))
                inv.update(balance=due_balance, status=status_inv)

                print(f'Fees Payment Counts: {pmt_counts};  Status: {status}; Last Receipt No: {last["receipt_no"]}')
                messages.success(request, 'The Transaction is cancelled Successfully')
                if last["receipt_no"] is None:
                    return redirect(list_enrollments)
                else:
                    return redirect(preview_payments, sch_id=sch_id, receipt_no=last["receipt_no"])
                    # return redirect(payment_receipt, sch_id=sch_id, receipt_id=last["receipt_no"], action='preview')  # Pre Receipt Print

            elif descx == 'wallet deposit':
                trans.delete()
                return HttpResponse(f'{trans.descx} transaction is cancelled.')
            else:
                return HttpResponse(trans.descx)
                # return redirect(list_enrollments)
        else:
            messages.warning(request, 'The Transaction you want to cancel does NOT exists.')
            return redirect(list_enrollments)

    except FinancialTransactions.DoesNotExist:
        messages.error(request, 'The Transaction you want to cancel does NOT exists.')
        return redirect(list_enrollments)


def financial_transactions(request, action, enr_id, inv_no, trans_id=0):
    sch_id = schools(request)['sch_id']

    if action == 'delete':
        cancel_financial_transaction(request, sch_id, trans_id)

    # -- Debit Student with the Fee Amount
    if action == 'update':
        fee_acct = FeesAccounts.objects.get(school=sch_id, doc_type='invoice', doc_no=inv_no)
        fee_form = FeesAccountsForm(request.POST, instance=fee_acct)
        trans_id = fee_acct.transaction_id
    else:
        fee_form = FeesAccountsForm(request.POST or None)
    if fee_form.is_valid():
        fee = fee_form.save(commit=False)
        # NOTE: The replace is used to remove any comma in the amt_paid text before converting to flaot else error
        fee.amount = float(request.POST['amount'].replace(',', ''))
        fee.enrolled_id = enr_id
        fee.tr_type = 'Dr'
        fee.trans_date = request.POST.get('trans_date')
        fee.descx = request.POST.get('descx')
        fee.doc_type = 'invoice'
        fee.doc_no = request.POST['invoice_no']
        fee.transaction_id = trans_id
        fee.save()
    else:
        messages.warning(request, fee_form.errors)

    #  Create / Update Invoice for the Student
    if action == 'update':
        invoice = Invoice.objects.get(school=sch_id, invoice_no=inv_no)
        invoice_form = InvoiceForm(request.POST or None, instance=invoice)
    else:
        invoice_form = InvoiceForm(request.POST or None)
    if invoice_form.is_valid():
        inv = invoice_form.save(commit=False)
        discount = float(request.POST['discount'].replace(',', ''))
        inv.amount = float(request.POST['amount'].replace(',', '')) # REPLACE remove any comma in the amt_paid text
        inv.due_date = ap_due_date(request)
        inv.balance = (inv.amount - discount)
        inv.enrolled_id = enr_id
        inv.package_id = request.POST['fee_pkg']
        inv.status = 'np'
        inv.transaction_id = trans_id
        inv.discount = discount
        inv.save()
    else:
        messages.error(request, invoice_form.errors)

    return None


def ap_due_date(request):
    date_now = datetime.date.today()

    sch_id = request.POST['school']
    timeline = request.POST['timeline']
    session_id = request.POST['session']

    term = AcademicSessions.objects.values('term_id').filter(id=session_id, status='Active',
                                                             sch_id=sch_id).first()  # filter returns queryset
    if term:
        # print('Term: ', term['term_id'])
        term_id = term['term_id']

        date = AcademicCalender.objects.values('cs_start_dt').filter(school=sch_id, timeline=timeline, term_id=term_id)[
            0]
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
    f1 = (Q(status='enrolled') | Q(status='paid') | Q(status='paying') | Q(status='returned')) & Q(school_id=sch_id)
    students_enrolled = Enrollments.objects.filter(f1).order_by('school_id', 'classroom_id', 'student__surname')

    context = {'enrollments': students_enrolled}
    return render(request, 'student-enrolled-list.html', context)


def next_payment_number(sch_id):
    """ Generate next wallet ID number"""
    pay = WalletPayments.objects.values('payment_id').order_by('school_id', 'payment_id').last()
    if pay is None:
        payment_id = 1
    else:
        payment_id = int(pay['payment_id']) + 1

    return payment_id


def student_wallet(request, action, deposit_amt, sch_id, stud_id, trans_id=0):
    """ Generate a Deposit ID Number from Wallet Deposit.
        Save Amount Deposited into WalletDeposits and WalletAccounts
        A Student Wallet comprises:
            Wallets
            WalletPayments
            WalletAccounts
     """
    if action == 'credit':
        status = 'deposit'
        tr_type = 'cr'
    elif action == 'debit':
        status = 'withdrawal'
        tr_type = 'dr'

    amt_paid = float(request.POST['amt_paid'].replace(',', ''))

    payment_id = next_payment_number(sch_id)

    form = WalletPaymentForm(request.POST or None)
    if form.is_valid():
        pmt = form.save(commit=False)
        pmt.amt_paid = deposit_amt
        pmt.payment_id = payment_id
        pmt.status = status
        pmt.transaction_id =trans_id
        try:
            pmt.save()
        except IntegrityError as e:
            messages.error(request, e.args)
            return {}
    else:
        messages.warning(request, form.errors)
        return {}

    """ Create Wallet if it has not been created 
        and Get the Wallet instance for the specified Student  """
    if not Wallets.objects.filter(school_id=sch_id, student_id=stud_id).exists(): # If Wallet does not exists
        wallet = Wallets.objects.create(school_id=sch_id, student_id=stud_id, transaction_id=trans_id)
    else:
        wallet = Wallets.objects.get(school_id=sch_id, student_id=stud_id)

    form = WalletAccountsForm(request.POST or None)
    if form.is_valid():
        acct = form.save(commit=False)
        acct.wallet_id = wallet.id
        acct.amt_paid = deposit_amt
        acct.tr_type = tr_type
        acct.payment_id = payment_id
        acct.transaction_id = trans_id
        try:
            acct.save()
        except IntegrityError as e:
            messages.error(request, e.args)
            return {}

        # Update accounts_id in WalletsDeposits
        pmt.accounts_id = acct.id
        pmt.balance = acct.runing['balance']
        pmt.save()
    else:
        messages.warning(request, form.errors)
        return {}

    return status


def get_or_create_bank_accounts(sch_id, status):
    """ Create Student Account (Wallet) and some major banks drop-down for the specified school
        Also, get the bank account drop-down for the specified school.
    """
    # Create Initial Bank Account drop-down list for the specified school if no account exists.
    if Banks.objects.filter(school=sch_id).count() <= 0:
        print(' ----- Creating Some Bank Account Drop-down list')
        Banks.objects.create(srl_no=1, bank_name='First Bank Account', status='active', school_id=sch_id)
        Banks.objects.create(srl_no=2, bank_name='Zenith Account', status='active', school_id=sch_id)
        Banks.objects.create(srl_no=3, bank_name='FCMB Account', status='active', school_id=sch_id)
        Banks.objects.create(srl_no=4, bank_name='GTB Account', status='active', school_id=sch_id)

    # Create Student Wallet drop-down for listing for the specified school if it has not been created.
    if not Banks.objects.filter(school=sch_id, bank_name='Student Wallet').exists():
        print(' ----- Creating Student Wallet (Account for Drop-Down list')
        accounts = Banks.objects.get_or_create(srl_no=5, bank_name='Student Wallet', status='active', school_id=sch_id)
        print(accounts)

    # Get Bank Accounts for drop-down list
    bank = Banks.objects.filter(status=status)

    return bank


from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseNotFound


def pdf_print_preview(request, sch_id, receipt_no):
    """
    THIS FUNCTION IS FOR TESTING
    Test Result is good. The function can be used to download or display PDF file

    The FileSystemStorage sets the base_url to the project’s MEDIA_ROOT.
    That means the file should be save in apps.media folder
    """
    fs = FileSystemStorage()
    filename = 'ngs_receipt.pdf'
    if fs.exists(filename):
        with fs.open(filename) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="nsg_receipt.pdf"'
            response['Content-Disposition'] = 'inline; filename="nsg_receipt.pdf"'
            return response
    else:
        return HttpResponseNotFound('The requested pdf was not found in our server.')



def print_pdf_receipt(request, sch_id, stud_id=0, receipt_no=0):
    sch = SchoolProfiles.objects.get(sch_id=sch_id)
    receipt_name = f"receipt-{sch_id}{stud_id}.pdf".lower()
    file_name = os.path.join(CORE_DIR, 'apps\\financials\\documents\\' + receipt_name)

    receipt_created = create_pdf_receipt(request, file_name, sch, stud_id=stud_id, receipt_id=receipt_no)  # Create PDF Receipt file

    if receipt_created:
        if request.GET.get('btn_print'):
            try:
                os.startfile(file_name, "print") # Print the file in the file_name location
                # Sleeping the program for 5 seconds so as to account the
                # steady processing of the print operation.
                sleep(5)
                # for p in psutil.process_iter():  # Close Acrobat after printing the PDF
                #    if 'AcroRd' in str(p):
                #        p.kill()
            except:
                messages.error(request, 'ALERT: Receipt could not be printed! Please ensure  \
                that associated PDF reader software is installed in this system.')

        elif request.GET.get('btn_preview'):
            try:
                os.startfile(file_name, "open")
                # sleep(15)
            except FileNotFoundError as e:
                messages.error(request, e.strerror)
            except:
                messages.error(request, 'ALERT: Receipt could not be preview or printed! ')

    return redirect(preview_payments,  sch_id=sch_id, receipt_no=receipt_no)  #  HTML Receipt Payment Preview


@transaction.atomic
def student_payment(request, stud_id):
    sch_id = schools(request)['sch_id']
    enrolled = Enrollments.objects.filter(school=sch_id, student_id=stud_id).order_by('id').last()
    # stud_id = enrolled.student_id
    enr_id = enrolled.id

    bank_id = request.POST.get('bank')
    if bank_id is None: bank_id = 0

    try:
        pay_into = Banks.objects.values('bank_name').get(id=bank_id)
    except:
        pay_into = {'bank_name': ''}

    f1 = Q(student_id=stud_id) & Q(school_id=sch_id) & (Q(status='np') | Q(status='pp'))
    inv = Invoice.objects.values('id', 'invoice_no', 'descx', 'amount', 'discount', 'balance').filter(f1).order_by('invoice_no')

    if request.method == 'POST':
        cur_sesx_id = get_cur_session(sch_id)
        # NOTE: The 'replace' is used to remove any comma in the amt_paid text before converting to flaat else error
        amt_paying = float(request.POST['amt_paid'].replace(',', ''))

        if pay_into['bank_name'] == 'Student Wallet':
            trans_id = create_tranaction(request, desc='wallet deposit', sch_id=sch_id, stud_id=stud_id)
            student_wallet(request, 'credit', amt_paying,  sch_id, stud_id, trans_id)
            return redirect(wallet_account, stud_id=stud_id)
        else:
            trans_id = create_tranaction(request, desc='fee payment', sch_id=sch_id, stud_id=stud_id)
            receipt_no = generate_receipt_no()  # Generate the next Receipt No
            inv_count = inv.count()
            # for i in inv:
            for x, i in enumerate(inv, start=1):
                if amt_paying <= 0:
                    break
                else:
                    inv_p = process_invoice(amt_paying, i, sch_id, stud_id)
                    amt_paying = inv_p['pay_bal']

                inv_no = inv_p['invoice_no']
                inv_bal = inv_p['inv_bal']
                status = inv_p['status']

                form = FeesAccountsForm(request.POST or None)
                if form.is_valid():
                    fee_acct = form.save(commit=False)
                    fee_acct.trans_date = request.POST.get('pmt_date')
                    fee_acct.descx = inv_p['descx']
                    fee_acct.amount = -abs(inv_p['amt_paid'])
                    fee_acct.tr_type = 'cr'
                    fee_acct.doc_type = 'receipt'
                    fee_acct.doc_no = receipt_no
                    fee_acct.transaction_id = trans_id
                    fee_acct.save()
                else:
                    messages.error(request, form.errors)

                payment = FeePaymentForm(request.POST or None)
                if payment.is_valid():
                    pmt = payment.save(commit=False)

                    pmt.session_id = cur_sesx_id['sesx_id']
                    pmt.invoice_id = i['id']
                    pmt.invoice_no = inv_no
                    pmt.receipt_no = receipt_no
                    pmt.status = status
                    pmt.pmt_descx = inv_p['descx']
                    pmt.amt_paid = inv_p['amt_paid']
                    pmt.transaction_id = trans_id
                    pmt.save()

                    if status == 'pp':
                        enr_status = 'paying'
                    elif status == 'pf':
                        enr_status = 'paid'

                    Invoice.objects.filter(school=sch_id, invoice_no=inv_no).update(balance=inv_bal, status=status)
                    Enrollments.objects.filter(school=sch_id, id=enr_id).update(last_rcpt_no=receipt_no, status=enr_status)
                    updated = Students.objects.filter(school=sch_id, id=stud_id).update(reg_status='active')

                    msg1 = ''
                    msg2 = ''
                    if updated:
                        msg1 = 'Student Fee Payment is successful. '

                    # Credit student Wallet with excess balance
                    if amt_paying > 0 and inv_count == x and status == 'pf':
                        created = student_wallet(request, 'credit', amt_paying, sch_id, stud_id, trans_id)
                        if created:
                            msg2 = 'Also, The student Wallet is Credited with the Balance of ' + str(amt_paying)
                        amt_paying = 0

                    msg = msg1
                    if msg2: msg = msg + msg2
                    messages.success(request, msg)

                    if x == inv_count:
                        return redirect(preview_payments, sch_id=sch_id, receipt_no=receipt_no)  # HTML Receipt Payment Preview

                else:
                    print(payment.errors)
                    messages.warning(request, payment.errors)

        return redirect(list_enrollments)

    else:
        header = 'Receive Payment'
        wallet = {}
        timeline = {}

        paymethod = PaymentMethods.objects.all()
        bank = get_or_create_bank_accounts(sch_id, status='active')
        try:
            timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
            wallet_bal = Wallets.objects.get(school=sch_id, student=stud_id).wallet['balance']
            if wallet_bal is None: wallet_bal = 0.00
            wallet = {'wallet_bal': wallet_bal}
        except:
            if not wallet:  wallet = {'wallet_bal': 0.00}

        pay_descx = ''
        for index, invoice in enumerate(inv, start=1):
            pay_descx = pay_descx + invoice['descx']
            if inv.count() > 1 and index < inv.count():
                pay_descx = pay_descx + '; \n'
            # print(index, pay_descx)

        context = {'header': header, 'enrolled': enrolled, 'timeline': timeline, 'paymethods': paymethod, 'banks': bank,
                   'descx': pay_descx, 'student': wallet}
        return render(request, 'student-payment.html', context)


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
    inv_disc = float(inv['discount'])
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
        # Generate Payment Description by Concatenating string and also set payment status
        # to either Full Payment or Partial payment
        status = 'pf'
        pay_count = FeesPayments.objects.filter(invoice_no=inv_no, school_id=sch_id, student_id=stud_id).count()
        if pay_count == 0:
            inv_descx = 'Full Payment: - ' + inv_descx
        else:
            inv_descx = 'Bal Payment: - ' + inv_descx

    result = {'invoice_no': inv_no, 'inv_bal': inv_bal, 'amt_paid': amt_paid, 'status': status,
              'pay_bal': amt_paying, 'descx': inv_descx}
    return result


def generate_receipt_no():
    p = FeesPayments.objects.values('receipt_no').order_by('school_id', 'id').last()
    if p is None:
        recpt_no = 1
    else:
        recpt_no = int(p['receipt_no']) + 1

    return recpt_no


def ap_package_amount(pkg_id, sch_id):
    pkg_amt = FeesPackage.objects.filter(id=pkg_id, school=sch_id).first().total_fees
    if not pkg_amt:
        pkg_amt = 0

    return pkg_amt


def ap_invoice_no(sch_id):
    inv_no = 0

    try:
        last_inv_no = Invoice.objects.filter(school=sch_id).order_by('invoice_no').last().invoice_no
        print(f'===========  Last Invoice No : {last_inv_no}  retrieved =====================')
    except AttributeError:
        inv_no = 1
        last_inv_no = 0
        print(f' ----- Initial Invoice No: {last_inv_no}')

    if last_inv_no:
        inv_no = int(last_inv_no) + 1

    return inv_no


def invoice_amount(request, pkg_id):
    sch = schools(request)
    print(sch['sch_id'])

    inv_amt = ap_package_amount(pkg_id, sch['sch_id'])
    inv_no = ap_invoice_no(sch['sch_id'])
    reg_no = generate_reg_no(request, jsonx=False)

    return JsonResponse({"inv_amount": inv_amt, 'inv_no': inv_no, 'reg_no': reg_no})


def wallet_account(request, stud_id, **kwargs):
    sch_id = schools(request)['sch_id']

    if request.method == 'GET':
        if kwargs:
            print('Key-Word Argument is entered')
        try:
            wallet = Wallets.objects.get(school_id=sch_id, student_id=stud_id)
            enrolled = Enrollments.objects.get(school_id=sch_id, student_id=stud_id)
            class_room = enrolled.classroom.class_abr
            context = {'wallet': wallet, 'class_room': class_room}
        except:
            context = {}
        # print(wallet.accounts.all())
        return render(request, 'wallet-accounts.html', context)


def create_pdf_receipt(request, file_name, sch, receipt_id, stud_id):
    from reportlab.lib.pagesizes import letter
    from apps.pdf_templates import pdf_receipt_template

    receipt = canvas.Canvas(file_name, pagesize=letter)
    receipt = pdf_receipt_template(request, receipt, sch, receipt_id)  # run the template
    result = False

    receipt.showPage()
    try:
        receipt.save()
        result = True
    except PermissionError as e:
        if e.strerror == 'Permission denied':
            messages.error(request, 'A previous receipt for this student is open. To Preview or Print another one, you have to close the previous one.')
        else:
            messages.error(request, e.strerror)

    return result


def preview_payments(request, sch_id=0, receipt_no=0):
    """ HTML RECEIPT Print Preview and Statements """

    f1 = Q(school_id=sch_id) & Q(receipt_no=receipt_no)
    fees = FeesPayments.objects.filter(f1).order_by('invoice_no')
    total = FeesPayments.objects.filter(f1).aggregate(amt_paid=Sum('amt_paid'))

    if total['amt_paid'] is None:
        total = {'amt_paid': 0.00}

    # Get the distinct invoice_no in FeesPayment for the specified receipt No
    inv_nos = FeesPayments.objects.filter(f1).values('invoice_no').order_by("invoice_no").distinct()

    wallet_amt = 0
    if fees:
        trans_id = fees.last().transaction_id
        stud_id = fees.first().student_id
        f2 = Q(school_id=sch_id) & Q(student_id=stud_id)
        stud_pmts = FeesPayments.objects.filter(f2).order_by('pmt_date', 'id')
        tot_sum = Invoice.objects.filter(f2).aggregate(due_fee=Sum(F('amount')-F('discount')), discount=Sum('discount'))
        due_date = Invoice.objects.filter(f2).values('due_date').order_by('due_date').last()

        # Get the Previous Total Payments for the specified invoice no excluding the current receipt no
        f3 = Q(school_id=sch_id) & Q(student_id=stud_id) & Q(invoice_no__in=inv_nos) & Q(receipt_no__lt=receipt_no)
        prv_fees_paid = FeesPayments.objects.filter(f3).order_by('receipt_no').aggregate(fees_paid=Sum('amt_paid'))

        wallet_credited = WalletPayments.objects.filter(transaction_id=trans_id).first()
        if wallet_credited:
            wallet_amt = wallet_credited.amt_paid

        if request.GET.get('recall'):
            print(request.GET.get('recall'))
            messages.info(request, f'The transaction with Receipt No: {receipt_no} is Re-Called')

    tot_amt_paid = total['amt_paid'] + wallet_amt

    context = {'fees': fees, 'total_amt_paid': tot_amt_paid, 'wallet_credited': wallet_amt, 'pmts': stud_pmts,
               'previous': prv_fees_paid, 'due_date': due_date, 'total': tot_sum}
    return render(request, 'payment-receipt-preview.html', context)

