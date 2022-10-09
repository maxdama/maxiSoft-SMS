from datetime import date
from django.contrib.auth.models import User, Group
from django.db import models
from apps.settings.models import SchoolProfiles


class Departments(models.Model):
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, null=True, blank=True, unique=False)
    name = models.CharField(max_length=30, unique=False, blank=True)

    class Meta:
        db_table = "apps_Departments"
        constraints = [
            models.UniqueConstraint(fields=['school', 'name'], name="unq_school_dept"),
        ]
    """
    def __str__(self):
        return "%s %s" % (str(self.school), self.name)
    """


class Employees(models.Model):
    """Custom table created to store information about Employees of an organisation"""
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, null=True, blank=True, unique=False)
    department = models.ForeignKey(Departments, on_delete=models.SET_NULL, null=True, blank=True, unique=False)
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, unique=True, null=True, blank=True)
    staff_no = models.CharField(max_length=25, unique=True, blank=True, db_index=True)
    title = models.CharField(max_length=10, blank=True, null=True)
    surname = models.CharField(max_length=30, unique=False, blank=True)
    other_names = models.CharField(max_length=60, unique=False, null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, db_index=True)
    dob = models.DateField(null=True, blank=True)
    marital_status = models.CharField(max_length=10, null=True, blank=True)
    mobile_no1 = models.CharField(max_length=30, null=True, blank=True)
    mobile_no2 = models.CharField(max_length=30, null=True, blank=True)
    email_addr = models.EmailField(null=True, blank=True)
    resid_addr = models.CharField(max_length=150, null=True, blank=True)
    resid_city = models.CharField(max_length=35, null=True, blank=True)
    resid_state = models.CharField(max_length=25, null=True, blank=True)
    depart = models.CharField(max_length=25, null=True, blank=True, unique=False)
    position = models.CharField(max_length=25, null=True, blank=True, unique=False)
    hire_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, blank=True)
    # lga_origin =
    # state_origin =
    # country_origin =

    def __str__(self):
        return "%s %s %s %s %s" % (self.staff_no, self.surname, self.other_names, self.gender, self.dob)

    class Meta:
        db_table = "apps_Employees"

    @property
    def age(self):
        if self.dob is not None:
            age = date.today().year - self.dob.year
            return age

    @property
    def years_worked(self):
        if self.hire_date is not None:
            age = date.today().year - self.hire_date.year
            return age


class Workgroup(models.Model):
    """The Position model is used in conjunction with the Django Group model. The Employee Position is store in
        Group, and it's related to the Position model that has the specific school id. The is so that the
        Staff Position of specified school can be filtered """
    objects = None
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True, unique=True)
    test = models.ForeignKey
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, null=True, blank=True, unique=False)

    class Meta:
        db_table = "apps_Workgroup"