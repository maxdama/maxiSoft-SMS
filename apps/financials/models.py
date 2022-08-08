from django.db import models

# Create your models here.
from django.db.models import Q, Count

from apps.settings.models import SchoolProfiles
from apps.students.models import Enrollments, Students


class FeesPackage(models.Model):
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    description = models.CharField(max_length=200)
    pkg_type = models.CharField(max_length=35, null=True, blank=True)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)

    @property
    def inv(self):
        i_count = 0
        qf = Q(school_id=self.school) & Q(package_id=self.id) & Q(status='np')
        i_count = Invoice.objects.filter(qf).aggregate(counter=Count('id'))

        return i_count

    def __str__(self):
        return self.description + ' ' + str(self.total_fees) + ' ' + self.status + ' ' + str(self.inv['counter'])

    class Meta:
        db_table = "apps_FeesPackage"
        ordering = ['school', 'id']
        constraints = [
            models.UniqueConstraint(fields=['school', 'description'], name="school_descx_unq"),
        ]


class FeesPackageDetails(models.Model):
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    package = models.ForeignKey(FeesPackage, on_delete=models.CASCADE, related_name='fee_details')
    item_no = models.IntegerField(unique=False, null=True, blank=True)
    item_descx = models.CharField(max_length=50)
    qty = models.IntegerField()
    unit_value = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.item_no) + ' ' + self.item_descx + ' ' + str(self.qty) + ' ' + str(self.amount)

    class Meta:
        db_table = "apps_FeesPackageDetails"
        ordering = ['school', 'id']


class FinancialTransactions(models.Model):
    trans_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False)
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='enrollment', unique=False, null=True, blank=True)
    invoice_no = models.IntegerField(null=True, blank=True)
    receipt_no = models.CharField(max_length=60, null=True, blank=True)
    descx = models.CharField(max_length=250)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    run_bal = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    tr_type = models.CharField(max_length=10)

    def __str__(self):
        return str(self.trans_date) + ' ' + self.descx + ' ' + str(self.tr_type) + ' ' + str(self.amount)

    class Meta:
        db_table = "apps_FinancialTransactions"
        ordering = ['school', 'id']


class Invoice(models.Model):
    trans_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False)
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, unique=False)
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='invoice', unique=False, null=True, blank=True)
    package = models.ForeignKey(FeesPackage, on_delete=models.CASCADE, related_name='invoice', unique=False)
    invoice_no = models.IntegerField(null=True, blank=True)
    descx = models.CharField(max_length=250)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return str(self.invoice_no) + ' ' + self.descx + ' ' + str(self.amount) + ' ' + self.status

    class Meta:
        db_table = "apps_Invoice"
        ordering = ['school', 'invoice_no']
        constraints = [
            models.UniqueConstraint(fields=['school', 'invoice_no'], name="school_Invoice_unq"),
        ]





