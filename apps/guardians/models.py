from django.db import models
from apps.students import models as stud


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
