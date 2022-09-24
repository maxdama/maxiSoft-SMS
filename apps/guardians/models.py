from django.db import models
from django.db.models import F, Q
# from apps.students.models import Students
from apps.students import models as sm


# Create your models here.
class Guardians(models.Model):
    title = models.CharField(max_length=15, null=True)
    surname = models.CharField(max_length=35, null=False, db_index=True)
    other_names = models.CharField(max_length=70, null=True)
    gender = models.CharField(max_length=10, null=True, )
    res_addr = models.CharField(max_length=255, null=True)
    res_area = models.CharField(max_length=80, null=True)
    res_city = models.CharField(max_length=35, null=True)
    res_state = models.CharField(max_length=35, null=True)
    mobile_no1 = models.CharField(max_length=33, null=True)
    mobile_no2 = models.CharField(max_length=33, null=True)
    email = models.EmailField(max_length=255, unique=False, null=True)
    stays_together = models.BooleanField(null=True)
    relationship = models.CharField(max_length=20, null=True)
    created_on = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_on = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return "%s %s" % (self.surname, self.other_names)

    class Meta:
        db_table = "apps_Guardians"
        ordering = ['surname']

    @property
    def student(self):  # Get the ID Number of the last Student assigned to the Guardian of the specified row
        qry_crit = Q(guardian_id=self.id) & Q(reg_status='pending')
        stud_id_no = sm.Students.objects.filter(qry_crit).values(id_no=F('id')).last()
        #if stud_id_no['id_no'] is None:
        if stud_id_no is None:
            stud_id_no = {'id_no': 0}
        return stud_id_no


    """ 
    @property
    def last_inv(self):  # Last Invoice Amount
        # Get the Last Invoice Amount issued to Student in Invoice Table
        crit = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id=self.timeline) & Q(session_id=self.session)
        last_paid = Enrollments.objects.filter(crit).values(amt=F('invoice__amount')).order_by('invoice__invoice_no').last()
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return last_paid
    """
