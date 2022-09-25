from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
# from django.core import serializers
from django.db.models import Sum, Q, F
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from .models import Students, Enrollments
from apps.financials.models import FeesPackage, Invoice
from .forms import RegistrationForm, StudentsRegistrationNewForm, EnrollmentForm
from django.http import HttpResponse, JsonResponse
import datetime
import os
# import glob
from django.contrib import messages
from apps.guardians import views as g, models as gm
from ..financials.forms import FinancialTransactionsForm, InvoiceForm
from ..settings.models import AcademicTimeLine, ClassRooms, AcademicSessions, SchoolProfiles
from django.db import transaction, IntegrityError
from ..utils import schools, default_image_restore


# Create your views here.
def increment_reg_no():
    last_reg_no = Students.objects.all().order_by('id').last()
    if not last_reg_no:
        return 'NGS' + str(datetime.date.today().year) + str(datetime.date.today().month).zfill(2) + '000'

    reg_id_str = last_reg_no.reg_no
    reg_no_int = int(reg_id_str[9:12])
    new_reg_no = reg_no_int + 1
    reg_id = 'NGS' + str(str(datetime.date.today().year)) + str(datetime.date.today().month).zfill(2) + str(
        new_reg_no).zfill(3)

    return reg_id


@login_required
def student_list(request):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    title = 'Registration'
    default_image_restore(request)
    # Request all the Student.
    qrycrit = (~Q(reg_status='graduated'))
    student = Students.objects.filter(qrycrit).order_by('-id')
    # enrl = Enrollments.objects.all().select_related('student')
    # print(enrl[0].student.first_name)
    try:
        acada_yr = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
    except AcademicTimeLine.DoesNotExist:
        messages.info(request,
                      'Student Registration List can not be viewed now:  The school Academic Year have not been set. Please consult with your Software Administrator to set it up.')
        return render(request, 'student/students-list.html', {'title': title})

    # Put the data into the context
    context = {
        'title': title, 'students': student, 'acada_yr': acada_yr.descx
    }
    return render(request, 'student/students-list.html', context)


def update_student_register(reg_id, request):
    stud = Students.objects.get(id=reg_id)
    school = schools(request)
    sch_id = school['sch_id']

    # stud.reg_no = reg_no
    stud.surname = request.POST['surname']
    stud.first_name = request.POST['first_name']
    stud.middle_name = request.POST['middle_name']
    stud.gender = request.POST['gender']
    stud.dob = request.POST['dob']
    stud.bloodgroup = request.POST['bloodgroup']
    stud.religion = request.POST['religion']
    stud.email = request.POST['email']
    stud.phone_no = request.POST['phoneno']
    stud.lga_origin = request.POST['lga']
    stud.state_origin = request.POST['state']
    stud.nationality = request.POST['nationality']
    if request.FILES:
        if len(stud.stud_pic) > 0:
            os.remove(stud.stud_pic.path)

        stud.stud_pic = request.FILES['stud_pic']

    if stud.reg_steps == 1:
        stud.reg_status = 'pending'

    stud_reg = stud.save()

    return stud


def delete_student(request, reg_id):
    # try:
    student = Students.objects.get(pk=reg_id)
    if student.reg_status == 'pending':
        try:
            if len(student.stud_pic) > 0:
                os.remove(student.stud_pic.path)  # Remove pictue file from Images folder
        except:
            pass

        student.delete()
        messages.success(request, 'Student Record deleted')
    else:
        messages.info(request, 'Student Record can not be deleted')
    # except FileNotFoundError:
    #    messages.warning(request, 'Delete Operation Failed.  The record is retained.')
    # except:
    #    messages.error(request, 'Delete operation Failed.')

    return redirect(student_list)

# TODO: This function form_register should be deleted. It has been replaced
@login_required
def form_register(request):
    print('Runing: form_register')
    gad_id = 0
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    print(f'----- School ID Number:  {sch_id}')
    if request.method == 'POST':
        print('----- Checking if Form is Valid')
        form = RegistrationForm(request.POST or None, request.FILES or None)

        if form.is_valid():
            print('----- Form is Valid')
            if request.POST['reg_id']:
                stud_obj = update_student_register(request.POST['reg_id'], request)
                opr = 'update'
                print('   Update Student Registration . . . ')

                gad_id = stud_obj.g_id_id
                if gad_id is None:
                    gad_id = 0
            else:
                # form.instance.reg_no = increment_reg_no()
                form.instance.reg_steps = 1
                form.instance.middle_name = request.POST['middle_name']
                form.instance.gender = request.POST['gender']
                form.instance.bloodgroup = request.POST['bloodgroup']
                form.instance.religion = request.POST['religion']
                form.instance.email = request.POST['email']
                form.instance.phone_no = request.POST['phoneno']
                form.instance.lga_origin = request.POST['lga']
                form.instance.state_origin = request.POST['state']
                form.instance.nationality = request.POST['nationality']
                form.instance.reg_status = 'pending'
                stud_obj = form.save()
                opr = 'new'
                print('   New Student Registration . . . ')

            if request.POST.get("save_pause"):
                if stud_obj:
                    if opr == 'new':
                        messages.success(request, 'The registration is not Complete yet, it is pending  ')
                        messages.success(request, 'Student registration Saved. ')
                    else:
                        messages.success(request, 'Student register Updated ')
                else:
                    messages.warning(request, 'Save operation failed')

                return redirect(student_list)

            elif request.POST.get("save_continue"):
                if opr == 'new':
                    messages.success(request, 'Assign Guardian to the Student')
                    messages.success(request, 'Student registration Saved. ')
                else:
                    messages.success(request, 'Student register Updated ')

                return redirect('guardian', gad_id=gad_id, reg_id=stud_obj.pk)
        else:
            print('----- The Form is NOT Valid')
            messages.warning(request, 'The Student registration was NOT Saved or Updated.')
            messages.warning(request, 'The Form is NOT Valid !!! ')
            return render(request, "student/reg-student-biodata.html", {'sch_id': sch_id, 'form': form})
            return redirect(student_list)
    else:
        default_image_restore(request)
        context = {'sch_id': sch_id}
        return render(request, "student/reg-student-biodata.html", context)


@login_required
def new_student_registration(request):
    print('Runing: New_Student_Registration')

    gad_id = 0
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    if not school['profile_exists']:
        messages.warning(request, 'THE SCHOOL PROFILE HAS NOT BEEN CREATED.  You can not proceed with this  '
                                  'operation until your Software Admin  creates it.')
        return render(request, "student/reg-student-biodata.html", {'student': request.POST, 'sch_id': sch_id})

    print(f'----- School ID Number:  {sch_id}')

    if request.method == "POST":
        print('----- Post Request method')
        if request.POST['reg_id']:
            print('----- Get Student Record for Update ')
            stud_id = request.POST['reg_id']
            stud_data = Students.objects.get(id=stud_id)
            student = StudentsRegistrationNewForm(request.POST, instance=stud_data)
            mode = 'edit'
            print('----- Student Record for Update Retrieved ')
            gad_id = stud_data.guardian_id
            print(f'----- Guardian ID Retrieved: {gad_id} ')
            if gad_id is None:
                gad_id = 0
                print(f'----- Guardian ID NOT Retrieved: {gad_id}')
        else:
            student = StudentsRegistrationNewForm(request.POST, request.FILES)
            mode = 'new'

        if student.is_valid():
            print('----- Form is Valid')
            stud = student.save(commit=False)
            stud.reg_steps = 1
            stud.school_id = request.POST['school']
            stud_assign_others(request, stud, mode)
            try:
                print('----- Saving Student Record. ')
                stud.save()
            except IntegrityError as e:
                print(f'----- Integrity Error Occurred:  {e}')
                msg = 'INTEGRITY ERROR:  insert or update on table "apps_Students" may have violates foreign key ' \
                      'constraint.  The current School ID may not be present in table "apps_SchoolProfiles'
                messages.error(request, msg)
                return render(request, "student/reg-student-biodata.html", {'student': request.POST, 'sch_id': sch_id})

            print('----- Student Record is SAVED')

            if request.POST.get("save_pause"):
                if stud:
                    if mode == 'new':
                        messages.success(request, 'The registration is not Complete yet, it is pending  ')
                        messages.success(request, 'Student registration Saved. ')
                    else:
                        messages.success(request, 'Student register Updated ')
                else:
                    messages.warning(request, 'Save operation failed')

                return redirect(student_list)

            elif request.POST.get("save_continue"):
                if mode == 'new':
                    messages.info(request, 'Please assign a Guardian to the Student')
                    messages.success(request, 'Student registration Saved. ')
                else:
                    messages.success(request, 'Student register Updated ')

                return redirect('guardian', gad_id=gad_id, reg_id=stud.pk)
        else:
            return render(request, "student/reg-student-biodata.html", {'student': request.POST, 'sch_id': sch_id})
    else:
        print('----- Get Request method')
        default_image_restore(request)
        context = {'sch_id': sch_id}
        return render(request, "student/reg-student-biodata.html", context)


def stud_assign_others(request, stud, mode="new"):
    stud.middle_name = request.POST['middle_name']
    stud.religion = request.POST['religion']
    stud.email = request.POST['email']
    stud.bloodgroup = request.POST['bloodgroup']
    stud.phone_no = request.POST['phoneno']
    stud.lga_origin = request.POST['lga']
    stud.state_origin = request.POST['state']
    stud.nationality = request.POST['nationality']

    if request.FILES:
        if len(stud.stud_pic) > 0 and mode == "edit":
            os.remove(stud.stud_pic.path)

        stud.stud_pic = request.FILES['stud_pic']

    if stud.reg_steps == 1 and request.POST['reg_status'] == '':
        print('Req_Status Value = "" ')
        stud.reg_status = 'pending'

    return None


def view_student_for_update(request, reg_id):
    if reg_id is None:
        reg_id = request.GET.get('id', '')
    student = Students.objects.get(id=reg_id)

    sch_id = student.school_id
    if sch_id == None: sch_id = 0

    context = {
        'reg_no': reg_id, 'name': student.surname, 'date': student.dob, 'student': student, 'sch_id': sch_id
    }
    return render(request, "student/reg-student-biodata.html", context)


@login_required
def continue_registration(request, reg_id, reg_step):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    print('Reg Step:')
    print(reg_step)

    try:
        student = Students.objects.get(id=reg_id, reg_steps=reg_step)
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)
        classes = ClassRooms.objects.filter(profile__sch_id=sch_id, status='active').order_by('levels')
        fees = FeesPackage.objects.values('id', 'description', 'total_fees').filter(status='Active', school=sch_id, pkg_type__icontains='new')
        sessions = AcademicSessions.objects.values('id', 'term_id', 'descx').filter(sch_id=sch_id, status='Active').order_by('term_id')

        context = {'student': student, 'timeline': timeline, 'classes': classes, 'fees': fees, 'sessions': sessions}

        if reg_step == 1:
            try:
                # Query Guardian with Student Guardian ID and if successful request financial Enrollment Form
                # otherwise, an exception is thrown that request the Guardian form
                guardian = gm.Guardians.objects.get(id=student.guardian_id or None)
                if guardian:
                    context = {'guardian': guardian, 'student': student, 'timeline': timeline}

                return render(request, "financial/student-enrollment.html", context)

            except gm.Guardians.DoesNotExist:

                guardians = gm.Guardians.objects.all().only('surname', 'other_names').order_by('surname')
                context2 = { 'gad_list': guardians}
                context.update(context2)  # The update is use to update context2 to context ( Concatenate )
                messages.info(request, "Please Enter or Select Parent / Guardian for the Student")
                return render(request, "guardians/reg-guardians-biodata.html", context)

            except Exception as e:
                raise e
                return redirect(student_list)
                # raise Http404

        elif reg_step == 2:
            return render(request, "financial/student-enrollment.html", context)

        elif reg_step == 3:
            context = {
                'student': student, 'timeline': timeline
            }
            return render(request, "financial/student-enrollment.html", context)

    except Students.DoesNotExist:
        return HttpResponse('Student Record Does not exists')
    except AcademicTimeLine.DoesNotExist:
        messages.info(request, "The Acadamic Timeline might have expired or has not been setup. "
                               "You can not do Student Enrollment now until the Timeline issue is resolved. "
                               "Please contact your systems admin")
        return redirect(student_list)

    except AcademicTimeLine.MultipleObjectsReturned:
        messages.warning(request, "The Academic Timeline was not Setup correctly. There is more than one Active session"
                         " in the timeline. You can not do Student Enrollment now until the Timeline issue is resolved."
                         " Please contact your Software Admin")

        return redirect(student_list)


@login_required
def list_students_enrolled(request):
    sch_id = schools(request)

    # print("==============  List Student Enrolled  =================================")
    context = {}

    # enrolled_students = Enrollments.objects.filter(status='Enrolled', school=sch_id).select_related('student', 'session', 'classroom')
    enrolled_students = Invoice.objects.filter(school=sch_id, enrolled__status='Enrolled').select_related('student',
                                                                                                          'enrolled')

    # due_amt = Enrollments.objects.filter(reg_no='NGS202204000', school_id=1).aggregate(amt_due=Sum('invoice__amount'))
    # print(due_amt)
    # students = Enrollments.objects.values('reg_no',).annotate(total=Sum('invoice__amount'),).order_by()
    # enrolled_students = Enrollments.objects.filter(school=sch_id, status='Enrolled', ).annotate(total=Sum('invoice__amount', filter=Q(invoice__status='np')), ).order_by('reg_no', 'total',)
    # print(enrolled_students)
    # MyModel.objects.values(renamed_value=F('cryptic_value_name'))  # F example
    '''
    query_filter = Q(reg_no='NGS202204000') & Q(school_id=1) & (Q(invoice__status='pf') | Q(invoice__status='pf'))
    due_date = Enrollments.objects.filter(query_filter).values(due=F('invoice__due_date')).first()
    print(due_date)
    if due_date is None:
        print(datetime.date.today())
    '''

    context = {
        'enrollments': enrolled_students
    }
    return render(request, 'student/student-enrolled-list.html', context)


def generate_reg_no(request, jsonx=True):
    if request.method == 'GET':

        try:
            reg_id_str = Enrollments.objects.exclude(reg_no__isnull=True).last().reg_no

        except AttributeError:
            reg_id = 'NGS' + str(datetime.date.today().year) + str(datetime.date.today().month).zfill(2) + '000'
            reg_id_str = False
            print(f'=============== Checking out for Error: {reg_id} =========================')

        if reg_id_str:
            reg_no_int = int(reg_id_str[9:12])
            new_reg_no = reg_no_int + 1
            reg_id = 'NGS' + str(str(datetime.date.today().year)) + str(datetime.date.today().month).zfill(2) + str(
                new_reg_no).zfill(3)

        if jsonx:
            return JsonResponse({"new_reg_no": reg_id})
        else:
            return reg_id
    else:
        return JsonResponse({'new_reg_no': ''})


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

    if last_inv_no:
        inv_no = int(last_inv_no) + 1

    return inv_no


def invoice_amount(request, pkg_id):
    sch_id = schools(request)

    inv_amt = ap_package_amount(pkg_id, sch_id)
    inv_no = ap_invoice_no(sch_id)
    reg_no = generate_reg_no(request, jsonx=False)

    return JsonResponse({"inv_amount": inv_amt, 'inv_no': inv_no, 'reg_no': reg_no})
