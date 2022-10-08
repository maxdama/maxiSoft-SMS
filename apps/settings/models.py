from datetime import date

from django.db import models


# Create your models here.
from django.db.models import Q, F


class SchoolProfiles(models.Model):
    objects = None
    sch_id = models.IntegerField(unique=True, db_index=True, primary_key=True)
    rc_no = models.CharField(max_length=35, unique=True, null=True)
    sch_name = models.CharField(max_length=300, unique=True, null=False, db_index=True)
    name_abr = models.CharField(max_length=5, unique=False, null=True, blank=True, db_index=True)
    sch_addr = models.CharField(max_length=500, null=True, blank=True)
    phone_no = models.CharField(max_length=33, null=True, blank=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, null=True, db_index=True)
    start_date = models.DateField(default=None, null=True, blank=True, db_index=True)
    prop_name = models.CharField(max_length=80, null=True, blank=True, db_index=True)
    sch_motor = models.CharField(max_length=200, null=True, blank=True)
    sch_logo = models.ImageField(upload_to='images', default='images/static/schoo-log-education.webp', null=True, blank=True)
    no_classrooms = models.IntegerField(unique=False, null=True, blank=True)

    def __str__(self):
        return self.sch_id, self.sch_name

    class Meta:
        db_table = "apps_SchoolProfiles"
        ordering = ['sch_id']


class ClassRooms(models.Model):
    profile = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, null=True, blank=True)
    class_name = models.CharField(max_length=55)
    class_abr = models.CharField(max_length=5)
    arm = models.CharField(max_length=5)
    status = models.CharField(max_length=10)
    levels = models.IntegerField()

    class Meta:
        unique_together = ('profile', 'class_abr', 'arm',)
        db_table = "apps_ClassRooms"
        ordering = ['profile', 'levels']


class AcademicSessions(models.Model):
    sch_id = models.IntegerField(unique=False, db_index=True)
    term_id = models.BigIntegerField()
    descx = models.CharField(max_length=15, unique=True, null=False)
    status = models.CharField(max_length=15, null=False)

    def __str__(self):
        return str(self.term_id)

    class Meta:
        db_table = "apps_AcademicSessions"
        ordering = ['status', 'term_id']


class AcademicTimeLine(models.Model):
    sch_id = models.IntegerField(unique=False, db_index=True)
    descx = models.CharField(max_length=25, db_index=True, unique=False)
    st_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    ed_dt = models.DateField(null=True, unique=False)
    status = models.CharField(max_length=15, null=False, default='Inactive', unique=False, db_index=True)
    s1_starts = models.DateField(default=None, null=True, blank=True)
    s1_ends = models.DateField(default=None, null=True, blank=True)
    s2_starts = models.DateField(default=None, null=True, blank=True)
    s2_ends = models.DateField(default=None, null=True, blank=True)
    s3_starts = models.DateField(default=None, null=True, blank=True)
    s3_ends = models.DateField(default=None, null=True, blank=True)

    @property
    def term(self):
        sch_term = {"idx": 1, "descx": '1st-Term'}
        """
        Get the Term_id by comparing the current date that fall between the cs_start_dt and cs_end_dt
        if no match then compare current date with holiday period and add 1 to term_id to get the next term
        if next term is greater than 3 then next term is 1. (i.e. That is first term).
        Use the term_id (t_id) to query AcademicSessions to get the ID and Descx which is returned
        """
        t_query = Q(sch_id=self.sch_id) & Q(cs_start_dt__lte=(date.today())) & Q(cs_end_dt__gte=(date.today()))
        term_id = AcademicCalender.objects.filter(t_query).values(idx=F('term_id')).first() # Get Term_id from Academic Calender base on the current date
        if not term_id:
            t_query = Q(sch_id=self.sch_id) & Q(hs_start_dt__lte=(date.today())) & Q(hs_end_dt__gte=(date.today()))
            term_id = AcademicCalender.objects.filter(t_query).values(idx=F('term_id')).first()
            if term_id:
                t_id = term_id['idx'] + 1
                if t_id > 4: t_id = 1
            else:
                t_id = 1
        else:
            t_id = term_id['idx']

        s_query = Q(sch_id=self.sch_id) & Q(term_id=t_id) & Q(status='Active')
        sch_term = AcademicSessions.objects.filter(s_query).values(idx=F('id'), descxx=F('descx')).first()
        # print(t_id, sch_term)
        return sch_term

    def __str__(self):
        return self.descx, self.status

    class Meta:
        db_table = "apps_AcademicTimeLine"
        ordering = ['descx']


class AcademicCalender(models.Model):
    sch_id = models.IntegerField(unique=False, null=True, blank=True)
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False, blank=True, null=True)
    timeline = models.ForeignKey(AcademicTimeLine, on_delete=models.RESTRICT, null=True, blank=True, unique=False, db_constraint=False)
    acad_yr = models.CharField(max_length=30, unique=False, null=False)
    start_dt = models.DateField(default=None, null=False, blank=True, db_index=True)
    end_dt = models.DateField(default=None, null=False, blank=True, db_index=True)
    term_id = models.IntegerField(unique=False, db_index=True)
    cs_start_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    cs_end_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    mb_start_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    mb_end_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    hs_start_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    hs_end_dt = models.DateField(default=None, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=15, null=True)
    created_on = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_on = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.term_id

    class Meta:
        db_table = "apps_AcademicCalender"
        ordering = ['school', 'status', 'term_id']



