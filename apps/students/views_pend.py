from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from apps.students.models import Students
from . forms import StudentForm, RegistrationForm, ImageForm
from django.http import HttpResponse
import datetime
from core import settings as s


def increment_reg_no():
    last_reg_no = Students.objects.all().order_by('id').last()
    if not last_reg_no:
        return 'NGS' + str(datetime.date.today().year) + str(datetime.date.today().month).zfill(2) + '000'

    reg_id_str = last_reg_no.reg_no
    reg_no_int = int(reg_id_str[9:12])
    new_reg_no = reg_no_int + 1
    reg_id = 'NGS' + str(str(datetime.date.today().year)) + str(datetime.date.today().month).zfill(2) + str(new_reg_no).zfill(3)

    return reg_id


# Create your views here.
@login_required
def student_list(request):
    title = 'Register'
    # Request all the Student.
    student = Students.objects.all()
    # Put the data into the context
    context = {
        'title':title,
        'students': student,
    }
    return render(request, 'student/students-list.html', context)


def save_student(request):
    # form = StudentForm(request.POST or None)
    # if form.is_valid():
    last_student = Students.objects.order_by('reg_no').last()
    if last_student is not None:
        reg_no = int(last_student.reg_no) + 1
    else:
        reg_no = 0

        # form.instance.reg_no = 11
        # form.instance.reg_steps = 1
        # new_reg = form.save()
        # return new_reg

    sur_name = request.POST.get('surname')
    first_name = request.POST.get('first_name')
    middle_name = request.POST.get('middle_name')
    dob = request.POST.get('dob')
    gender = request.POST.get('gender')
    email = request.POST.get('email')
    reg_steps = 1

    student_data = Students(reg_no=reg_no, surname=sur_name,  first_name=first_name, middle_name=middle_name,
                            dob=dob, gender=gender, email=email, reg_steps=reg_steps)
    return HttpResponse(f'Studdnt Data: {student_data}')
    student_data.save()
    # if student_data is not None:
    return HttpResponse(f'Registration No: {reg_no} ')

    #return {'not_student': form}
    # return render(request, 'student/new_registration.html', context)


def update_student_register(reg_no, request):

    stud = Students.objects.get(reg_no=reg_no)
    stud.reg_no = reg_no
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
        stud.stud_pic = request.FILES['stud_pic']

    if stud.reg_steps == 1:
        stud.reg_status = 'pending'

    stud_reg = stud.save()

    # return HttpResponse(f'Registration No: {stud_reg} ')
    return stud


def student_registered(request, reg_no):
    if reg_no is None:
        reg_no = request.GET.get('reg_no', '')
    student = Students.objects.get(reg_no=reg_no)

    context = {
        'reg_no': reg_no,
        'name': student.surname,
        'date': student.dob,
        'student': student
    }
    #return HttpResponse(f'Student Record for Update: <br> {context} ')
    return render(request, "student/reg-student-biodata.html", context)


def new_student_register(request):
    if request.method == 'POST':
        new_student = save_student(request)
        return HttpResponse(new_student)
        # return render(request, 'student/new_registration.html', {'student': new_student})
        # reg_no = 2
        # return HttpResponse("Data Saved")
    else:
        #  Students.objects.all().delete()
        # return render(request, "student/new_registration.html")
        return render(request, "student/reg_studentinfo.html")


def form_register(request):
    reg_no = 0

    if request.method == 'POST':
        form = RegistrationForm(request.POST or None,  request.FILES or None)

        if form.is_valid():
            if request.POST['reg_no']:
                new_reg = update_student_register(request.POST['reg_no'], request)
            else:
                form.instance.reg_no = increment_reg_no()
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
                # form.instance.stud_pic = request.FILES('stud_pic')

                form.save()
                new_reg = form.instance

            if request.POST.get("save_pause"):
                return redirect(student_list)


            elif request.POST.get("save_continue"):
                return HttpResponse(f'Save and continue: <br>')
    else:
        # Students.objects.all().delete()
        # return HttpResponse(f'Media Root:   {s.MEDIA_ROOT} <br> Core Dir:   {s.CORE_DIR} <br> Base Dir:   {s.BASE_DIR}')
        return render(request, "student/reg-student-biodata.html")


def returned_student_register(request):
    msg = None
    success = False


def image_upload_view(request):
    """Process images uploaded by users"""
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Get the current instance object to display in the template
            img_obj = form.instance
            return render(request, 'student/index.html', {'form': form, 'img_obj': img_obj})
    else:
        form = ImageForm()
    return render(request, 'student/index.html', {'form': form})
