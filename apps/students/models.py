from django.db import models
from django.db.models import Sum, Q, F

from apps.guardians import models as gm
from apps.settings import models as sm
from datetime import date
import datetime


# Create your models here.

class Students(models.Model):
    objects = None
    school = models.ForeignKey(sm.SchoolProfiles, on_delete=models.CASCADE, null=True, blank=True, unique=False)
    reg_no = models.CharField(max_length=50, unique=True, db_index=True, null=True, blank=True)
    surname = models.CharField(max_length=40, db_index=True)
    first_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40, null=True)
    guardian = models.ForeignKey(gm.Guardians, on_delete=models.RESTRICT, null=True, blank=True, unique=False)
    guardian_is = models.CharField(max_length=25, null=True, blank=True)
    stud_pic = models.ImageField(upload_to='images', default='images/static/default.png', null=True, blank=True)
    dob = models.DateField(default=None, null=True, blank=True, db_index=True)
    gender = models.CharField(max_length=8, db_index=True)
    email = models.EmailField(max_length=255, unique=False, null=True, db_index=True)
    phone_no = models.CharField(max_length=33, null=True, db_index=True)
    bloodgroup = models.CharField(max_length=5, null=True, blank=True)
    religion = models.CharField(max_length=15, null=True, blank=True)
    not_with_guard = models.BooleanField(default=False)  # Field to hold boolean value indicating if student is living with guardian or not
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
    objects = None
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, related_name='enrollment', null=False, blank=True, unique=False)
    school = models.ForeignKey(sm.SchoolProfiles, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    timeline = models.ForeignKey(sm.AcademicTimeLine, on_delete=models.RESTRICT, blank=True, unique=False)
    session = models.ForeignKey(sm.AcademicSessions, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    reg_no = models.CharField(max_length=50, unique=False, null=False)
    classroom = models.ForeignKey(sm.ClassRooms, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    trans_date = models.DateField(default=None, null=False, blank=True, db_index=True)
    fee_pkg = models.BigIntegerField(default=0)
    status = models.CharField(max_length=50, null=True, db_index=True)
    first_inv_no = models.BigIntegerField(null=True, blank=True, unique=True, default=None)
    last_rcpt_no = models.CharField(max_length=65, null=True, blank=True, unique=True, default=None)

    @property
    def inv(self):  # Invoice Amount (Cumlative Sum)
        # Get the Total Invoice Amount for the specified student and Class
        crit = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        crit2 = Q(Invoice__enrolled_id=self.id)
        inv_amt = Enrollments.objects.filter(crit).aggregate(amt=Sum('invoice__amount'))
        if inv_amt['amt'] is None:
            inv_amt = {'amt': 0.00}
        # print(inv_amt)
        return inv_amt

    @property
    def paid(self):  # Cumulative Amount Paid
        # paid_amt = 25000
        # Calculate Total Amount Due of the Student in the current row
        qf1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        qf2 = (Q(payments__status='pp') | Q(payments__status='pf')) & Q(payments__enrolled_id__lte=self.id)
        paid_amt = Enrollments.objects.filter(qf1).aggregate(amt=Sum('payments__amt_paid', filter=qf2))
        # print(paid_amt['due'])
        if paid_amt['amt'] is None:
            paid_amt = {'amt': 0.00}
        return paid_amt

    @property  # Total Amount Due
    def tot_amt(self):
        # tot_amt = 25000
        # Calculate Total Amount Due of the Student in the current row
        qf1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        qf2 = (Q(invoice__status='np') | Q(invoice__status='pp'))
        due_amt = Enrollments.objects.filter(qf1).aggregate(due=Sum('invoice__balance', filter=qf2))
        # print(due_amt['due'])
        if due_amt['due'] is None:
            due_amt = {'due': 0.00}
        return due_amt

    @property  # Due Date
    def due(self):
        due_dt = '20-03-2022'
        query_criteria = Q(reg_no=self.reg_no) & Q(school_id=self.school) & \
                         ((Q(invoice__status='np') | Q(invoice__status='pp'))) & Q(timeline_id=self.timeline) & Q(session_id=self.session)
        due_dt = Enrollments.objects.filter(query_criteria).values(date=F('invoice__due_date')).order_by('invoice__due_date').first()

        if due_dt is None:
            due_dt = {'date': datetime.date.today()}
        # print(due_dt)
        return due_dt

    @property
    def last_inv(self):  # Last Invoice Amount
        # Get the Last Invoice Amount issued to Student in Invoice Table
        crit = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id=self.timeline) & Q(session_id=self.session)
        last_paid = Enrollments.objects.filter(crit).values(amt=F('invoice__amount')).order_by('invoice__invoice_no').last()
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return last_paid

    @property  # Term Cumulative payment
    def term_pmt(self):
        # Get the Cumulative payment of the term for the specified Student
        crit = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        crit1 = Q(payments__session_id=self.session_id) & Q(payments__student_id=self.student_id) & Q(payments__school_id=self.school_id)
        last_paid = Enrollments.objects.filter(crit).aggregate(amt=Sum('payments__amt_paid', filter=crit1))
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return last_paid

    @property  # Last Payment Amount
    def last_pmt(self):
        # Get the Last Amount Paid in Payments Table for the specified Student and Class
        crit = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        crit1 = Q(payments__receipt_no=self.last_rcpt_no) & Q(payments__student_id=self.student_id) & Q(payments__school_id=self.school_id)
        last_paid = Enrollments.objects.filter(crit).aggregate(amt=Sum('payments__amt_paid', filter=crit1))
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return last_paid

    @property  # Last Payment Date
    def last_paymt(self):
        # Get the last payment date of every student of the current academic year
        # last_pmt_dt = '20-03-2022'
        criteria = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        # last_pmt_dt = Enrollments.objects.filter(criteria).values(date=F('payments__pmt_date')).order_by('payments__pmt_date').last()
        try:
            last_pmt_dt = Enrollments.objects.filter(criteria).values(date=F('payments__pmt_date'))\
                .exclude(payments__pmt_date__isnull=True).order_by('payments__pmt_date').last()

            # print(last_pmt_dt)
            if last_pmt_dt['date'] is None:
                last_pmt_dt = {'date': datetime.date.today()}
        except:
            last_pmt_dt = {'date': datetime.date.today()}

        return last_pmt_dt

    def __str__(self):
        return self.reg_no + ' ' + str(self.trans_date) + ' ' + self.status + ' ' + str(self.tot_amt['due']) + ' ' + str(self.due['date'])

    class Meta:
        db_table = "apps_Enrollments"
        ordering = ['school_id', 'reg_no']
        # unique_together = ('school_id', 'session', 'reg_no', 'classroom')
        constraints = [
            models.UniqueConstraint(fields=['school_id', 'timeline', 'session', 'reg_no'], name="unq_regno_class"),
            models.UniqueConstraint(fields=['school_id', 'timeline', 'session', 'student'], name="unq_stud_class"),
        ]
