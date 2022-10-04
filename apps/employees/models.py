from django.contrib.auth.models import User
from django.db import models


class Employees(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, unique=True, null=True, blank=True)
    staff_no = models.CharField(max_length=25, unique=True, blank=True, db_index=True)
    surname = models.CharField(max_length=30, unique=False, blank=True)
    other_names = models.CharField(max_length=60, unique=False, null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, db_index=True)
    dob = models.DateField(null=True, blank=True)
    marital_status = models.CharField(max_length=10, null=True, blank=True)
    mobile_no = models.CharField(max_length=30, null=True, blank=True)
    email_addr = models.EmailField(null=True, blank=True)
    resid_addr = models.CharField(max_length=150, null=True, blank=True)
    resid_city = models.CharField(max_length=35, null=True, blank=True)
    resid_state = models.CharField(max_length=25, null=True, blank=True)
    # lga_origin =
    # state_origin =
    # country_origin =

    class Meta:
        db_table = "apps_Employees"
