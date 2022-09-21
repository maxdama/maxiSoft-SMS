from django.contrib.auth.decorators import login_required
from django.db.models import RestrictedError
from django.shortcuts import render, redirect
from apps.students import models as sm
from . import models as gm
from . forms import GuardianForm
from django.contrib import messages


def update_guardian(request):
    gad_id = request.POST['gad_id']
    guardian = {'gad_id': gad_id}

    try:
        # Get objects from Guardians models and store in guardian
        guardian = gm.Guardians.objects.get(pk=gad_id)

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
        guardian.relationship = request.POST['relationship']
        # guardian.stays_together = request.POST['stays_together']
        guardian.save()

        return guardian

    except gm.Guardians.DoesNotExist:
        return guardian


# Create your views here.
def new_guardian(request):

    if request.method == 'POST':
        reg_id = request.POST['reg_id']
        student = sm.Students.objects.get(pk=reg_id)

        form = GuardianForm(request.POST)
        if form.is_valid():
            g_id = request.POST['gad_id']

            if request.POST['gad_id']:    # Check if Guardian ID exists from POSTED form.
                guardian = update_guardian(request)  # Update Guardian model
                context = {'reg_id': reg_id, 'gad_id': request.POST['gad_id'], 'student': student, 'guardian': guardian}
                messages.success(request, "Update successfully.")
                # return render(request, 'student/reg-enrollment.html', context)
            else:
                # Get guardian model object–
                # guardian = form.save(commit=False)  # commit=False means that we don't want to save the guardian model yet#

                form.instance.title = request.POST['title']
                form.instance.res_addr = request.POST['res_addr']
                form.instance.res_area = request.POST['res_area']
                form.instance.res_city = request.POST['res_city']
                form.instance.res_state = request.POST['res_state']
                form.instance.mobile_no2 = request.POST['mobile_no2']
                form.instance.email = request.POST['email']
                # form.instance.stays_together = request.POST['stays_together']

                guardian = form.save()
                messages.success(request, "Saved successfully.")

            # Update Student Bio Data
            student.reg_steps = 2
            student.guardian_id = guardian.pk
            student.save()

            if request.POST.get("save_continue"):
                return redirect('new-enrollment', reg_id=reg_id) # Route through guardian-url to view_enrollment function below
            else:
                return redirect('guardians') # route through guardian-url to guardian_list below
        else:
            context = {'student': student, 'guardian': form }
            return render(request, 'guardians/reg-guardians-biodata.html', context)
    else:
        return render(request, 'guardians/reg-guardians-biodata.html')


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
def view_guardian(request, gad_id, reg_id):
    context = {}

    guardians = gm.Guardians.objects.all().only('surname', 'other_names').order_by('surname')
    if reg_id > 0:
        student = sm.Students.objects.get(pk=reg_id)
    elif reg_id == 0 and gad_id > 0:
        # Use guardian ID to get the ID of student assigned.
        student = sm.Students.objects.filter(guardian_id=gad_id, reg_status='pending').order_by('-id').last()
        print(student)
    context = {'student': student, 'gad_list': guardians}

    # if view_gad == `1 and stud_obj:`
    if gad_id > 0 and student:
        try:
            guardian = gm.Guardians.objects.get(pk=student.guardian_id)
            context = { 'student': student, 'guardian': guardian, 'gad_list': guardians }
        except gm.Guardians.DoesNotExist:
            gad_id = 0

    return render(request, 'guardians/reg-guardians-biodata.html', context)


@login_required
def guardian_list(request):
    title = 'Guardians'
    # Request all the Student.
    #if status == 'all':
    guardians = gm.Guardians.objects.all().order_by('-id')
    # Put the data into the context
    context = {
        'title':title,
        'guardians': guardians,
    }
    return render(request, 'guardians/guardians-list.html', context)



