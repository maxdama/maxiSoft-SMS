from django.contrib.auth.decorators import login_required
from django.db.models import RestrictedError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from apps.students import models as sm
from . import models as gm
from . forms import GuardianForm
from django.contrib import messages
from ..utils import schools

# Create your views here.


def update_guardian(request, sch_id):
    gad_id = request.POST['gad_id']
    guardian = {'gad_id': gad_id}

    try:
        # Get objects from Guardians models and store in guardian
        guardian = gm.Guardians.objects.get(pk=gad_id)

        guardian.school_id = sch_id
        guardian.title = request.POST['title']
        guardian.surname = request.POST['surname']
        guardian.other_names = request.POST['other_names']
        guardian.gender = request.POST['gender']
        guardian.res_addr = request.POST['res_addr']
        guardian.res_area = request.POST['res_area']
        guardian.res_city = request.POST['res_city']
        guardian.res_state = request.POST['res_state']
        guardian.mobile_no1 = request.POST['mobile_no1']
        guardian.mobile_no2 = request.POST['mobile_no2']
        guardian.email = request.POST['email']
        # guardian.relationship = request.POST['relationship']
        # guardian.stays_together = request.POST['stays_together']
        guardian.save()

        return guardian

    except gm.Guardians.DoesNotExist:
        return guardian


def student_update(request, student, guardian):

    print('Not Together CheckBox value: ')
    not_together = False
    chk_values = request.POST.getlist('not_with_guard')  # Get the list of Checkbox with the name enclosed
    for value in chk_values: # Loop through checkbox. In this case it's only one check box
        not_together = value

    print(not_together)
    student.reg_steps = 2
    student.guardian_id = guardian.pk
    student.not_with_guard = not_together
    student.guardian_is = request.POST['relationship']

    if not_together:  # Student is NOT living with Guardian or Parent
        #  Update Student Residential Address
        student.res_addr_l1 = request.POST['res_addr_l1']
        student.res_addr_l2 = request.POST['res_addr_l2']
        student.res_city = request.POST['stud_res_city']
    else:  # Student is living with Guardian or Parent
        #  Set Student Residence address to None
        student.res_addr_l1 = None
        student.res_addr_l2 = None
        student.res_city = None

    student.save()

    return None



@login_required
def new_guardian(request, oprx_type='edit-entry'):
    print('New Guardian: -- ')

    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    print(f'----- Operation Type:  {oprx_type}')
    reg_id = 0
    student = {}
    if request.method == 'POST':
        print('----- POST Request Method ')
        if oprx_type == 'new-entry':
            reg_id = request.POST['reg_id']
            student = sm.Students.objects.get(pk=reg_id)

        form = GuardianForm(request.POST)
        if form.is_valid():
            print('----- Valid Guardian Form Confirmation')
            g_id = request.POST['gad_id']

            if request.POST['gad_id']:    # Check if Guardian ID exists from form Posted then Update.
                # Update Guardian model
                guardian = update_guardian(request, sch_id)
                context = {'reg_id': reg_id, 'gad_id': request.POST['gad_id'], 'student': student, 'guardian': guardian}
                messages.success(request, "Guardian Updated successfully.")
                # return render(request, 'student/reg-enrollment.html', context)
            else:
                # New Guardian Entry
                # Get guardian model object–
                # guardian = form.save(commit=False)  # commit=False means that we don't want to save the guardian model yet#
                form.instance.title = request.POST['title']
                form.instance.res_addr = request.POST['res_addr']
                form.instance.res_area = request.POST['res_area']
                form.instance.res_city = request.POST['res_city']
                form.instance.res_state = request.POST['res_state']
                form.instance.mobile_no2 = request.POST['mobile_no2']
                form.instance.email = request.POST['email']
                form.instance.school_id = sch_id

                guardian = form.save()
                messages.success(request, "Guardian Saved successfully.")

            if oprx_type == 'new-entry':
                # Update Student Bio Data
                student_update(request, student, guardian)

            if request.POST.get("save_continue"):
                return redirect('new-enrollment', reg_id=reg_id) # Route through guardian-url to view_enrollment function below
            else:
                return redirect('guardians') # route through guardian-url to guardian_list below
        else:
            print('----- Invalid Guardian Form Confirmation')
            context = {'student': student, 'guardian': form }
            return render(request, 'guardians/reg-guardians-biodata.html', context)
    else:
        return render(request, 'guardians/reg-guardians-biodata.html')


@login_required
def delete_guardian(request, gad_id):
    guardian = gm.Guardians.objects.get(pk=gad_id)
    if guardian:
        try:
            guardian.delete()
            messages.warning(request, 'Guardian Record deleted')

        except RestrictedError:
            messages.warning(request, 'Student is already assigned to this Guardian. Delete is Aborted')
            gad_id = None
    else:
        messages.info(request, 'Guardian Record can not be deleted')
    return redirect(guardian_list)


@login_required
def view_guardian_for_update(request, gad_id, stud_id, oprx_type='edit-entry'):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    print(oprx_type)

    context = {}
    children = []
    guardians = []

    if oprx_type == 'edit-entry':
        print('----- Query Children of this Parent  ')
        children = sm.Students.objects.filter(school_id=sch_id, guardian_id=gad_id)
        print(children)
    else:
        # list of Parents/Guardians for Selection
        guardians = gm.Guardians.objects.all().only('surname', 'other_names').order_by('surname')

    if stud_id > 0:
        student = sm.Students.objects.get(pk=stud_id)
    elif stud_id == 0 and gad_id > 0:
        # Use guardian ID to get the ID of the last student assigned and pending.
        student = sm.Students.objects.filter(guardian_id=gad_id, reg_status='pending').order_by('-id').last()
        print(student)

    context = {'student': student, 'gad_list': guardians, 'children': children, 'oprx_type':  oprx_type}

    if oprx_type == 'select-parent':
        guardian = gm.Guardians.objects.get(pk=gad_id)
        context2 ={'oprx_type': 'new-entry', 'guardian': guardian}
        context.update(context2)

    else:
        if gad_id > 0 and student:
            try:
                guardian = gm.Guardians.objects.get(pk=student.guardian_id)
                context = {'student': student, 'guardian': guardian, 'gad_list': guardians}

            except gm.Guardians.DoesNotExist:
                messages.warning(request, 'Guardian was not found for Update')
                guardian = gm.Guardians.objects.get(pk=gad_id)
                context = {'student': student, 'guardian': guardian, 'gad_list': guardians}
                gad_id = 0

            context1 = {'show_parent_child': True, 'children': children, 'oprx_type':  oprx_type}
            context.update(context1)

    return render(request, 'guardians/reg-guardians-biodata.html', context)


@login_required
def guardian_list(request):
    title = 'Guardians'

    guardians = gm.Guardians.objects.all().order_by('-id')  # Request all the Guardians.
    context = {'title':title, 'guardians': guardians, }

    return render(request, 'guardians/guardians-list.html', context)


def update_relationship(request):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    stud_id = request.POST['stud_id']
    card_id = request.POST['card_id']

    print(f'Student ID: {stud_id}')
    print('Testing Ajax URL POST Request . . .')
    msg = f'Student being Processed: ID= {stud_id}'

    student = sm.Students.objects.filter(school_id=sch_id, id=stud_id).update(guardian_id=None)

    if not student:
        card_id = 0

    return JsonResponse({'data': msg, 'card_id': card_id})
