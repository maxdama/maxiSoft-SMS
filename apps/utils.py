from django.contrib.auth import logout
from django.shortcuts import redirect
import shutil
import os.path
from os import path
import datetime
from apps.settings.models import AcademicSessions, AcademicCalender


def get_school_id(request):
    """ Gets the school ID from the login session. If the session has expired, the
        function Logs out the User and redirect the user to the Login Page.
    """
    sch_id = 0
    if request.session.has_key('school_id'):
        sch_id = request.session['school_id']
        return sch_id
    else:
        logout(request)
        return redirect("logout")


def default_image_restore(request):
    """ if the default picture file is not found in the static folder
        the function copy it from the images folder to the static folder.
        It ensures that the default student picture file is always in the
        static folder even if it is delete in the course of
        deleting a student record.
    """
    src_dir = "apps/media/images/"
    dst_dir = "apps/media/images/static"
    # files = [src_dir + 'default.png', src_dir + 'file2.txt', src_dir + 'file3.txt']
    files = [src_dir + 'default.png']

    if not path.exists(dst_dir + "/default.png"):
        for f in files:
            shutil.copy(f, dst_dir)

    return None


def get_cur_session(sch_id):
    """ Get the current Academic Session_id of the school specified using the current date as a criteria.
        The Term is first determine then after the term is used to get the session_id
    """

    sesx_id = 0
    # cur_date = '2017-09-15'
    cur_date = datetime.date.today()
    # TODO - Correction:  ensure that sch_id in AcademicCalener table is populated when setting up
    term = AcademicCalender.objects.filter(cs_start_dt__lte=cur_date, cs_end_dt__gte=cur_date).values('term_id', 'cs_start_dt').last()
    last_sessx = AcademicSessions.objects.filter(sch_id=sch_id, status='Active').values('term_id').order_by('sch_id','term_id').last()
    last_term = last_sessx['term_id']

    if term is not None:
        # print('School Period Payment')
        cur_term = term['term_id']
        sessx = AcademicSessions.objects.filter(term_id=cur_term, status='Active', sch_id=sch_id).values('id').last()
        sesx_id = sessx['id']
    else:
        holiday_end_date = AcademicCalender.objects.filter(cs_start_dt__lte=cur_date, hs_end_dt__gte=cur_date).values('hs_end_dt').last()
        if holiday_end_date is not None:
            # print('Holiday Period Payment')
            term = AcademicCalender.objects.filter(cs_start_dt__lte=cur_date, hs_end_dt__gte=cur_date).values('term_id').last()
            cur_term = term['term_id']
            sessx = AcademicSessions.objects.filter(term_id=cur_term, status='Active', sch_id=sch_id).values('id').last()
            sesx_id = sessx['id']

    if cur_term == last_term:
        next_term = AcademicSessions.objects.filter(sch_id=sch_id, status='Active').values('term_id').order_by('sch_id','term_id').first()['term_id']
        print(f'Next Term for the year: {next_term} ')
    else:
        next_term = cur_term + 1

    context = {'sesx_id': sesx_id, }

    return context
