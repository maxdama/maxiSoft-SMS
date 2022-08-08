from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import SchoolProfiles, AcademicSessions, AcademicTimeLine, AcademicCalender
from .forms import SchoolProfilesForm, AcademicTimelineForm, AcademicCalenderForm


# Create your views here.
def term_is_used(term_id):
    # term_used = Enrollments.objects.filter(term_id_id=term_id).exists()
    return False


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

    sch_id = request.session['school_id']
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

        context = {'acad': form,  'new_opr': new_opr, 'sch_id': sch_id, 'uid':uid}
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

            form = AcademicTimelineForm(request.POST or None,  instance=timeline)
            if form.is_valid():
                timeline = form.save(commit=False)
                timeline.save()
                sch_id = timeline.sch_id
            else:
                messages.warning(request, form.errors)
                form = AcademicTimelineForm(request.POST)
                context = {'sch_id': sch_id, "acad": form, 'new_opr': False, 'uid':uid}
                return render(request, 'setup/academic-timeline.html', context)

        return redirect(f"academic-timeline-list/{sch_id}")


def setup_school_terms(request):
    sch_id = 0
    if request.session.has_key('school_id'):
        sch_id = request.session['school_id']

    if not SchoolProfiles.objects.filter(sch_id=sch_id).exists():
        messages.info(request, 'Your School Profile must be entered first. Then after you can set the Session names.')
        return redirect('profile')

    data = {}
    if request.method == 'POST':
        sch_id = request.POST['sch_id']
        term_id = request.POST['term_id']
        descx = request.POST['descx'].strip()
        status = request.POST['status'].strip()

        if not AcademicSessions.objects.filter(sch_id=sch_id, term_id=term_id,
                                               descx=descx).exists():  # Search Object does not exists
            # Check if Term has been used in School Sessions or School Enrollment
            try:
                if term_is_used(term_id):
                    # Update the Term Status to Inactive
                    term = AcademicSessions.objects.filter(term_id=term_id, status='Active').update(status='In-Active')
                    if term:
                        messages.warning(request, 'Previous-Term record is In-Active')
                else:
                    # Delete the Term
                    term = AcademicSessions.objects.filter(term_id=term_id, status='Active').delete()
                    if term:
                        messages.info(request, 'Unused Term Record Deactivated')

                # create and save object
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
    # student = Students.objects.all().order_by('-id')
    # Put the data into the context
    context = {}
    return render(request, 'setup/list-academic-sessions.html', context)


def setup_academic_calender(request):
    sch_id = request.session['school_id']

    try:
        timeline = AcademicTimeLine.objects.get(status='active', sch_id=sch_id)  # Return the first row from the queryset
        context = {sch_id, timeline.id}

        sessxs = AcademicSessions.objects.filter(status='Active', sch_id=sch_id).order_by('term_id')
        if not sessxs:
            messages.info(request, 'You have been redirect: Your School Academic Session must be entered, followed by '
                                   'Academic Timeline or Period, before your School Academic Calender.')
            return redirect('school-terms')

        if request.method == 'POST':
            saved = False

            for s in sessxs:
                t = s.term_id
                # messages.info(request, f'Session Data:-  {s.term_id}')
                form = AcademicCalenderForm(request.POST or None)
                if form.is_valid():
                    cal = form.save(commit=False)
                    cal.term_id = request.POST[f'term_id_{t}']
                    cal.cs_start_dt = request.POST[f'st_dt_tm_{t}']
                    cal.cs_end_dt = request.POST[f'ed_dt_tm_{t}']
                    cal.mb_start_dt = request.POST[f'st_dt_mb_{t}']
                    cal.mb_end_dt = request.POST[f'ed_dt_mb_{t}']
                    cal.hs_start_dt = request.POST[f'st_dt_hd_{t}']
                    cal.hs_end_dt = request.POST[f'ed_dt_hd_{t}']

                    try:
                        cal.save()
                        if cal.id:
                            messages.info(request, f'Academic Calender Saved')
                            saved = True

                    except ValidationError as e:
                        messages.warning(request, f'Session {t} data is NOT saved:  You have to make sure that all the Starts and End dates are entered for the session. ')

                else:
                    messages.warning(request, form.errors)
                    return render(request, 'setup/academic-calender.html', { 'sch_id': sch_id, 'timeline': timeline, 'sessx': sessxs})

            else:
                if not form.errors and saved:
                    return redirect('list-sessions')
                else:
                    data = {
                        'sess': request.POST,
                        'sessx': sessxs,
                    }
                    return render(request, 'setup/academic-calender.html', data)

        else:
            data = {
                'sch_id': sch_id,
                'sessx': sessxs,
                'timeline': timeline,
            }
            return render(request, 'setup/academic-calender.html', data)



    except AcademicTimeLine.DoesNotExist:
        messages.info(request, 'You have been redirect: Please enter Your School  '
                               'Academic Timeline or Period, befor your School Academic Calender.')
        return redirect('academic-timeline')

    except Exception as e:
        messages.error(request, f'{type(e)}  The following Error Occured: {e.message}, ')
        return render(request, 'setup/academic-calender.html')


def setup_academic_calender_1(request):
    saved = False
    sch_id = request.session['school_id']

    try:
        terms = AcademicSessions.objects.filter(status='Active', sch_id=sch_id).order_by('term_id')
        if not terms:
            messages.info(request, 'You have been redirect: Your School Academic Session must be entered, followed by '
                                   'Academic Timeline or Period, befor your School Academic Calender.')
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
    if sch_id != request.session['school_id']:
        sch_id = request.session['school_id']

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


def setup_academic_calender_tabs(request):
    sch_id = request.session['school_id']
    sessx = AcademicSessions.objects.filter(status='Active', sch_id=sch_id).order_by('term_id')

    data = {'sessx': sessx}
    return render(request, 'setup/academic-calender.html', data)
    # return render(request, 'setup/calender-tabs.html', data)



