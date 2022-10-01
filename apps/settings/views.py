from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import SchoolProfiles, AcademicSessions, AcademicTimeLine, AcademicCalender, ClassRooms
from .forms import SchoolProfilesForm, AcademicTimelineForm, AcademicCalenderForm, ClassRoomsForm
from ..students.models import Enrollments
from ..utils import schools
# Create your views here.



def term_is_used(term_id):
    sx_used = False

    # sx = AcademicSessions.objects.values('id').get(term_id=term_id, status='Active')
    sx = AcademicSessions.objects.values('id').filter(term_id=term_id, status='Active').first()
    print(f'Academic Session: {sx}')
    if sx:
        print(sx)
        xin_enrolled = Enrollments.objects.filter(session_id=sx['id']).exists()
        if xin_enrolled:
            sx_used = True

    return sx_used


def to_words(fig):
    word = ['zero', 'First', 'Second', 'Third', 'Forth', 'Fifth', 'Sixth', 'Seventh', 'Eight', 'Nineth']
    return word[fig]


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def query_acadamic_years(sch_id):
    xstatus = 'Active'
    id = 8
    # sql = '''SELECT * FROM public."apps_AcadaYears" y WHERE y.status=%(0)s AND y.sch_id=%(1)s '''
    sql = '''SELECT * FROM public."apps_AcadaYears" y WHERE y.status=%s '''
    # cursor = connection.cursor()
    # instr = "'{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}'".format(softname, procversion, int(percent), exe, description, company, procurl)
    xcrit = "'{0}'".format(xstatus)
    # xcrit = "['{0}', {1}]".format(xstatus, sch_id)
    print(xcrit)
    with connection.cursor() as cursor:
        cursor.execute(sql % xcrit)
        rows = dictfetchall(cursor)
        # rows = cursor.fetchone()
        # rows = cursor.fetchall()

    return rows


def academic_timeline(request):
    # Initial call (GET) Display Academic timeline for Editing if data for school id is in table and status is 'Active'
    # otherwise a new Academic Year is saved into table
    # If POST opoeration, form data is saved and redirected to Academic List

    context = {}
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    if not SchoolProfiles.objects.filter(sch_id=sch_id).exists():
        messages.info(request, 'Your School Profile must be entered first. Then after you can enter Academic Timeline.')
        return redirect('profile')

    status = 'active'
    uid = None

    if request.method == 'GET':
        try:
            new_opr = False
            timeline = AcademicTimeLine.objects.get(sch_id=sch_id, status='active')
            form = AcademicTimelineForm(instance=timeline)
            uid = timeline.id
        except:
            new_opr = True
            data = {'sch_id': sch_id}
            form = AcademicTimelineForm(data)

        context = {'acad': form, 'new_opr': new_opr, 'sch_id': sch_id, 'uid': uid}
        return render(request, 'setup/academic-timeline.html', context)

    elif request.method == 'POST':

        if request.POST['save_action'] == 'new':

            form = AcademicTimelineForm(request.POST or None)
            if form.is_valid():
                timeline = form.save(commit=False)
                timeline.status = status
                timeline.save()

                sch_id = timeline.sch_id
                messages.success(request, "The School Academic timeline is saved")
            else:
                messages.warning(request, form.errors)
                form = AcademicTimelineForm(request.POST)

                context = {'sch_id': sch_id, "acad": form, 'new_opr': True}
                return render(request, 'setup/academic-timeline.html', context)

        elif request.POST['save_action'] == 'update':
            uid = request.POST['uid']
            timeline = AcademicTimeLine.objects.get(id=uid)

            form = AcademicTimelineForm(request.POST or None, instance=timeline)
            if form.is_valid():
                timeline = form.save(commit=False)
                timeline.save()
                sch_id = timeline.sch_id
            else:
                messages.warning(request, form.errors)
                form = AcademicTimelineForm(request.POST)
                context = {'sch_id': sch_id, "acad": form, 'new_opr': False, 'uid': uid}
                return render(request, 'setup/academic-timeline.html', context)

        return redirect(f"academic-timeline-list/{sch_id}")


def setup_school_terms(request):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    if not SchoolProfiles.objects.filter(sch_id=sch_id).exists():
        messages.info(request, 'Your School Profile must be entered first. Then after you can set the Session names.')
        return redirect('profile')

    data = {}
    if request.method == 'POST':
        sch_id = request.POST['sch_id']
        term_id = request.POST['term_id']
        descx = request.POST['descx'].strip()
        status = request.POST['status'].strip()

        # Check if DescX NOT EXISTS for the specified School and Term
        if not AcademicSessions.objects.filter(sch_id=sch_id, term_id=term_id, descx=descx).exists():

            try:
                # Check if Term has been used in Academic Calenders or School Enrollment
                if term_is_used(term_id):
                    # Update the Term Status to Inactive
                    term = AcademicSessions.objects.filter(term_id=term_id, status='Active').update(status='In-Active')
                    if term:
                        messages.warning(request, 'Previous-Term record is In-active')
                else:
                    # Delete the Term
                    term = AcademicSessions.objects.filter(term_id=term_id, status='Active').delete()
                    # Access Tuple and checking if delete was successful
                    if term[0] != 0:
                        messages.info(request, 'The previous Term Entry was Deleted')

                # create and save new Academic Session ( object )
                school_term = AcademicSessions(term_id=term_id, descx=descx, status=status, sch_id=sch_id)
                school_term.save()
                messages.success(request, 'New-Terms record Activated')

            # except Enrollments.RestrictedError:
            except RuntimeError:
                messages.error(request, 'An error occured')
        else:
            messages.info(request, 'No changes made')

    try:
        sch_prof = SchoolProfiles.objects.get(sch_id=sch_id)
        name = sch_prof.sch_name

    except:
        name = {}

    terms = AcademicSessions.objects.filter(status='Active').order_by('term_id')

    data = {
        'sch_id': sch_id,
        'sch_name': name,
        'terms': terms,
    }
    return render(request, 'setup/school-terms.html', data)


def list_academic_sessions(request):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    action = 'Add New'
    context = {}
    rows1 = {}

    timeline = AcademicTimeLine.objects.filter(sch_id=sch_id).order_by('-id')
    if AcademicTimeLine.objects.filter(sch_id=sch_id, status='active').exists():
        action = 'Update'

    tl = {'timeline': timeline}
    actx = {'action': action}

    context = {**tl, **actx}
    return render(request, 'setup/list-academic-sessions.html', context)


def map_form_fields(request, term_id, data):
    if data == 'cal_data':
        context = {
            "school": request.POST['school'],
            "timeline": request.POST['timeline'],
            "acad_yr": request.POST['acada_yr'],
            "start_dt": request.POST['start_dt'],
            "end_dt": request.POST['end_dt'],
            "term_id": request.POST[f'term_id_{term_id}'],
            "cs_start_dt": request.POST[f'st_dt_tm_{term_id}'],
            "cs_end_dt": request.POST[f'ed_dt_tm_{term_id}'],
            "mb_start_dt": request.POST[f'st_dt_mb_{term_id}'],
            "mb_end_dt": request.POST[f'ed_dt_mb_{term_id}'],
            "hs_start_dt": request.POST[f'st_dt_hd_{term_id}'],
            "hs_end_dt": request.POST[f'ed_dt_hd_{term_id}'],
            "status": "active"

        }
    elif data == 'date_data':

        if request.POST[f'ed_dt_hd_3']:
            end_dt = request.POST[f'ed_dt_hd_{term_id}']
        else:
            end_dt = request.POST['end_dt']

        if request.POST[f'st_dt_tm_1']:
            start_dt = request.POST[f'st_dt_tm_1']
        else:
            start_dt = request.POST['start_dt']

        context = {
            "sch_id": request.POST['sch_id'],
            "descx": request.POST['acada_yr'],
            "st_dt": start_dt,
            "ed_dt": end_dt,
            f"s{term_id}_starts": request.POST[f'st_dt_tm_{term_id}'],
            f"s{term_id}_ends": request.POST[f'ed_dt_tm_{term_id}']
        }

    return context


def setup_academic_calender(request):
    print('setup_academic_calener - Function ')

    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    try:
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id) # Return the first row from the queryset
        sessxs = AcademicSessions.objects.filter(status='Active', sch_id=sch_id).order_by('term_id').only("term_id", "descx")

        if not sessxs:
            messages.info(request, 'You have been redirect: Your School Academic Session must be entered, followed by '
                                   'Academic Timeline or Period, before your School Academic Calender.')
            return redirect('school-terms')

        if request.method == 'POST':
            saved = False

            for s in sessxs:
                t = s.term_id
                cal_data = map_form_fields(request, s.term_id, 'cal_data')
                date_data = map_form_fields(request, s.term_id, 'date_data')
                # print(date_data)

                try:
                    acad_cal = AcademicCalender.objects.get(school=sch_id, timeline=timeline.id, term_id=s.term_id)
                    # If acad_cal is not null (has data) then get AcademicCalender for update
                    form_cal = AcademicCalenderForm(cal_data or None, instance=acad_cal)
                    action = 'Updated'
                except:
                    # If acad_cal is null (no data) then save new form_data
                    form_cal = AcademicCalenderForm(cal_data or None)
                    action = 'Saved'

                form_tl = AcademicTimelineForm(date_data or None, instance=timeline)

                if form_cal.is_valid() and form_tl.is_valid():
                    acad_cal = form_cal.save(commit=False)

                    try:
                        acad_cal.save()  # Save or Update
                        acad_tl = form_tl.save()

                        if acad_cal.id and acad_tl.id:
                            saved = True
                            messages.info(request,
                                          f'Academic Calender for {timeline.descx} is {action} for {to_words(t)} Term')

                    except ValidationError as e:
                        messages.warning(request,
                                         f'Session {t} data is NOT saved:  You have to make sure that all the Starts and End dates are entered for the session. ')

                else:
                    messages.warning(request, form_cal.errors)
                    messages.warning(request, form_tl.errors)
                    return render(request, 'setup/academic-calender.html',
                                  {'sch_id': sch_id, 'timeline': timeline, 'sessx': sessxs})

            else:
                if not form_cal.errors and saved:
                    return redirect('list-sessions')
                else:
                    data = {
                        'sess': request.POST,
                        'sessx': sessxs,
                    }
                    return render(request, 'setup/academic-calender.html', data)

        else:
            print('----- Request Method: = GET')
            data = { 'sessx': sessxs, 'timeline': timeline,} # 'sch_id': sch_id,
            print(sessxs)
            for s in sessxs:
                try:
                    # acad_cal = AcademicCalender.objects.get(sch_id=sch_id, tl_id=timeline.id, term_id=s.term_id)
                    acad_cal = AcademicCalender.objects.get(school=sch_id, timeline=timeline.id, term_id=s.term_id)
                    print(acad_cal.acad_yr)
                    # form = AcademicCalenderForm(instance=acad_cal)
                    # tbl_data = map_form_fields(acad_cal, s.term_id, 'tbl_data')
                    if s.term_id == 1:
                        cal1 = {'cal1': acad_cal}
                    if s.term_id == 2:
                        cal2 = {'cal2': acad_cal}
                    if s.term_id == 3:
                        cal3 = {'cal3': acad_cal}

                    # print(f' TABLE: {acad_cal.cs_start_dt}')
                except Exception as e:
                    cal1={}
                    cal2={}
                    cal3={}

                    # print(f'An Error Occured: {e.message}')

            context = {**data, **cal1, **cal2, **cal3}

            # return render(request, 'setup/academic-calender.html', {**data, **value1})
            return render(request, 'setup/academic-calender.html', context)



    except AcademicTimeLine.DoesNotExist:
        messages.info(request, 'You have been redirect: Please enter Your School  '
                               'Academic Timeline or Period, before your School Academic Calender.')
        return redirect('academic-timeline')

    except Exception as e:
        messages.error(request, f'{type(e)}  The following Error Occured: {e.message} ')
        return render(request, 'setup/academic-calender.html')


def setup_academic_calender_1(request):
    saved = False
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    try:
        terms = AcademicSessions.objects.filter(status='Active', sch_id=sch_id).order_by('term_id')
        if not terms:
            messages.info(request, 'You have been redirect: Your School Academic Session must be entered, followed by '
                                   'Academic Timeline or Period, before your School Academic Calender.')
            return redirect('school-terms')
        time_line = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)  # Return the first row from the queryset
        # Acad_cal = AcademicCalender.objects.filter(AcademicTimeLine__sch_id=sch_id, AcademicTimeLine__status='active')
        # Acad_cal = AcademicCalender.objects.filter(AcademicTimeLine__in=time_line)

    except AcademicTimeLine.DoesNotExist:
        messages.info(request, 'You have been redirect: Please enter Your School  '
                               'Academic Timeline or Period, befor your School Academic Calender.')
        return redirect('academic-timeline')

    if request.method == 'POST':
        # t = 1
        # while t <= 3:
        for t in range(1, 4):
            acad_yr = request.POST['acada_yr']
            st_dt_acyr = request.POST['start_dt']
            ed_dt_acyr = request.POST['end_dt']
            # First Term
            term_id = request.POST[f'term_id_{t}']
            st_dt_term = request.POST[f'st_dt_tm_{t}']
            ed_dt_term = request.POST[f'ed_dt_tm_{t}']
            # Mid Term Break 1st Term
            st_dt_mb = request.POST[f'st_dt_mb_{t}']  # Start Date
            ed_dt_mb = request.POST[f'ed_dt_mb_{t}']  # End Date
            # 1st Term Holidays
            st_dt_h = request.POST[f'st_dt_hd_{t}']
            ed_dt_h = request.POST[f'ed_dt_hd_{t}']
            status = 'Active'

            num_word = to_words(t)

            try:
                acad_sess = AcademicCalender(sch_id=sch_id, acad_yr=acad_yr, start_dt=st_dt_acyr, end_dt=ed_dt_acyr,
                                             term_id=term_id, cs_start_dt=st_dt_term, cs_end_dt=ed_dt_term,
                                             mb_start_dt=st_dt_mb, mb_end_dt=ed_dt_mb,
                                             hs_start_dt=st_dt_h, hs_end_dt=ed_dt_h, status=status)
                acad_sess.save()
                if acad_sess.id:
                    saved = True
                    messages.info(request,
                                  f'Academic Calender {acad_yr} Saved for {num_word} Term:  Returned ID: {acad_sess.id}')

            except IntegrityError:
                messages.warning(request, f'An Integrity constraint occured while trying saving {num_word} Term')
            except ValidationError:
                messages.warning(request, f'Sessions without Date entries are not saved for {num_word} Term')

        else:
            if saved:
                return redirect('list-sessions')
            else:
                data = {
                    'sess': request.POST,
                    'sessx': terms,
                }
                return render(request, 'setup/academic-calender.html', data)

    else:
        data = {
            'sch_id': sch_id,
            'sessx': terms,
            'timeline': time_line,
        }
        return render(request, 'setup/academic-calender.html', data)


def list_academic_timeline(request, sch_id):
    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    timeline = AcademicTimeLine.objects.filter(sch_id=sch_id).order_by('-id')

    data = {'timelines': timeline}
    return render(request, 'setup/academic-timeline-list.html', data)


def setup_school_profile(request):
    # form = SchoolProfilesForm(request.POST or None)

    if request.method == 'POST':

        if request.POST['save_action'] == 'do_update':
            sch_id = request.POST['sch_id']
            action = "do_update"

            # prof = get_object_or_404(SchoolProfiles, sch_id=sch_id) # Works very well
            prof = SchoolProfiles.objects.get(sch_id=sch_id)  # Works very well execept for the 404 error display

            form = SchoolProfilesForm(request.POST or None, request.FILES or None, instance=prof)
            if form.is_valid():
                prof = form.save(commit=False)

                prof.save()
                messages.success(request, "Your School Profile is updated")
                context = {'form': form, 'action': action}

            else:
                form.errors
                messages.warning(request, form.errors)

        elif request.POST['save_action'] == 'do_new':
            form = SchoolProfilesForm(request.POST or None, request.FILES or None)
            if form.is_valid():
                form.save()
                messages.success(request, "The School Profile saved")
            else:
                messages.warning(request, form.errors)

        return redirect('profile')

    elif request.method == 'GET':
        sch_id = 0
        sch_logo = {}
        action = "do_new"

        if request.session.has_key('school_id'):
            username = request.session['user_name']
            sch_id = request.session['school_id']

        try:
            # sch_prof = get_object_or_404(SchoolProfiles, sch_id=sch_id) # this also works
            sch_prof = SchoolProfiles.objects.get(sch_id=sch_id)

            if sch_prof:
                action = "do_update"

            form = SchoolProfilesForm(instance=sch_prof)
            sch_logo = sch_prof.sch_logo

        except:
            data = {'sch_id': sch_id}
            form = SchoolProfilesForm(data)

        context = {'form': form, 'action': action, 'sch_logo': sch_logo}
        return render(request, 'setup/school-profile.html', context)


def setup_class_rooms(request):
    sch_id = 0
    prf_id = 0

    school = schools(request)
    sch_id = school['sch_id']
    if sch_id == 0:
        return redirect("logout")

    if not school['profile_exists']:
        messages.info(request, 'Your School Profile must be entered first, then after you can setup the Class Rooms.')
        return redirect('profile')

    context = {}
    if request.method == 'POST':
        prf = request.POST['profile']
        abr = request.POST['class_abr']
        arm = request.POST['arm']

        if request.POST['save_btn'] == 'delete':
            clsroom = 0
            try:
                clsroom = ClassRooms.objects.get(profile=prf, class_abr=abr, arm=arm)
                clsroom.delete()
                messages.success(request, 'The selected Class setup has been DELETED')

            except:
                if clsroom:
                    messages.warning(request, 'The selected Class can not be deleted now. It is being used at the moment')
                else:
                    messages.error(request, clsroom.errors)
        else:

            try:
                clsroom = ClassRooms.objects.get(profile=prf, class_abr=abr, arm=arm)
                classes = ClassRoomsForm(request.POST, instance=clsroom)

            except ClassRooms.DoesNotExist:
                classes = ClassRoomsForm(request.POST)

            if classes.is_valid():
                classes = classes.save(commit=False)
                classes.status = classes.status.lower()

                classes.save()
                messages.success(request, 'The Class Setup is SAVED')
            else:
                messages.error(request, classes.errors)

    classes = ClassRooms.objects.filter(profile__sch_id=sch_id).order_by('levels') # Query upward to the parent from the child in criteria school__sch_id=sch_id

    context = {'profile': prf_id, 'classes': classes}
    return render(request, 'setup/class-rooms.html', context)