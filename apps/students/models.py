from django.db import models

from apps.guardians import models as gm
from apps.settings import models as sm
from datetime import date


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

