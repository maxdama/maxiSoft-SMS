from django.db import models
from django.db.models import Sum, Q, F

from apps.guardians import models as gm
from apps.settings import models as sm
from datetime import date
import datetime


# Create your models here.

class Students(models.Model):
    school = models.ForeignKey(sm.SchoolProfiles, on_delete=models.CASCADE, null=True, blank=True, unique=False)
    reg_no = models.CharField(max_length=50, unique=True, db_index=True, null=True, blank=True)
    surname = models.CharField(max_length=40, db_index=True)
    first_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40, null=True)
    g_id = models.ForeignKey(gm.Guardians, on_delete=models.RESTRICT, null=True, blank=True, unique=False)
    stud_pic = models.ImageField(upload_to='images', default='images/static/default.png', null=True, blank=True)
    dob = models.DateField(default=None, null=True, blank=True, db_index=True)
    # age = models.IntegerField(default=None, null=True)
    gender = models.CharField(max_length=8, db_index=True)
    email = models.EmailField(max_length=255, unique=False, null=True, db_index=True)
    phone_no = models.CharField(max_length=33, null=True, db_index=True)
    bloodgroup = models.CharField(max_length=5, null=True, blank=True)
    religion = models.CharField(max_length=15, null=True, blank=True)
    res_addr_l1 = models.CharField(max_length=255, null=True)
    res_addr_l2 = models.CharField(max_length=100, null=True)
    res_city = models.CharField(max_length=35, null=True)
    state_origin = models.CharField(max_length=30, null=True)
    lga_origin = models.CharField(max_length=30, null=True)
    nationality = models.CharField(max_length=30, null=True)
    reg_steps = models.IntegerField(null=True)
    reg_status = models.CharField(max_length=50, null=True, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_on = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.surname + ' ' + self.first_name + ' ' + self.middle_name

    class Meta:
        db_table = "apps_Students"
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['school', 'reg_no'], name="school_regno_unq"),
        ]

    @property
    def age(self):
        if self.dob != None:
            age = date.today().year - self.dob.year
            return age


class Enrollments(models.Model):
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    school = models.ForeignKey(sm.SchoolProfiles, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    timeline = models.ForeignKey(sm.AcademicTimeLine, on_delete=models.RESTRICT, blank=True, unique=False)
    session = models.ForeignKey(sm.AcademicSessions, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    reg_no = models.CharField(max_length=50, unique=False, null=False)
    classroom = models.ForeignKey(sm.ClassRooms, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    trans_date = models.DateField(default=None, null=False, blank=True, db_index=True)
    fee_pkg = models.BigIntegerField(default=0)
    status = models.CharField(max_length=50, null=True, db_index=True)

    @property
    def due(self):
        due_dt = '20-03-2022'
        query_criteria = Q(reg_no=self.reg_no) & Q(school_id=self.school) & (Q(invoice__status='np') | Q(invoice__status='pp'))
        due_dt = Enrollments.objects.filter(query_criteria).values(date=F('invoice__due_date')).order_by('invoice__due_date').first()

        if due_dt is None:
            due_dt = {'date': datetime.date.today()}
        # print(due_dt)
        return due_dt

    @property
    def amount(self):
        # due_amt = 25000
        qf1 = Q(reg_no=self.reg_no) & Q(school_id=self.school)
        qf2 = Q(invoice__status='np') | Q(invoice__status='pp')
        due_amt = Enrollments.objects.filter(qf1).aggregate(due=Sum('invoice__amount', filter=qf2))
        # print(due_amt['due'])
        if due_amt['due'] is None:
            due_amt = {'due': 0.00}
        return due_amt

    def __str__(self):
        return self.reg_no + ' ' + str(self.trans_date) + ' ' + self.status + ' ' + str(self.amount['due']) + ' ' + str(self.due['date'])

    class Meta:
        db_table = "apps_Enrollments"
        ordering = ['school_id', 'reg_no']
        # unique_together = ('school_id', 'session', 'reg_no', 'classroom')
        constraints = [
            models.UniqueConstraint(fields=['school_id', 'timeline', 'reg_no'], name="regno_class_unx"),
            models.UniqueConstraint(fields=['school_id', 'timeline', 'student'], name="stud_class_unx"),
        ]
