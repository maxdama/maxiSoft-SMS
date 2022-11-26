from django.db import models

# Create your models here.
from django.db.models import Q, Count, Sum

from apps.settings.models import SchoolProfiles, ClassRooms, AcademicSessions
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
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='enrollment', unique=False,
                                 null=True, blank=True)
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
    objects = None
    trans_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False)
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, unique=False)
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='invoice', unique=False,
                                 null=True, blank=True)
    session = models.ForeignKey(AcademicSessions, on_delete=models.DO_NOTHING, unique=False, null=True, blank=True)
    package = models.ForeignKey(FeesPackage, on_delete=models.CASCADE, related_name='invoice', unique=False)
    invoice_no = models.BigIntegerField(null=True, blank=True)
    descx = models.CharField(max_length=250)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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


class PaymentMethods(models.Model):
    srl_no = models.IntegerField()
    pay_method = models.CharField(max_length=15, unique=True, null=False)

    def __str__(self):
        return str(self.pay_method)

    class Meta:
        db_table = "apps_PaymentMethods"
        ordering = ['srl_no']


class Banks(models.Model):
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    srl_no = models.IntegerField()
    bank_name = models.CharField(max_length=150, unique=True, null=False)
    status = models.CharField(max_length=15, unique=False, blank=True)
    trnx_count = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return str(self.srl_no) + ' ' + str(self.bank_name) + ' ' + str(self.status) + ' ' + str(self.trnx_count)

    class Meta:
        db_table = "apps_Banks"
        ordering = ['srl_no']


class Payments(models.Model):
    objects = None
    # pmt_id = models.BigIntegerField(unique=True, primary_key=True)
    receipt_no = models.CharField(max_length=65)
    invoice_no = models.IntegerField(null=True, blank=True)
    pmt_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False)
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, unique=False)
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                 null=False, blank=True)
    classroom = models.ForeignKey(ClassRooms, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                  null=True, blank=True)
    session = models.ForeignKey(AcademicSessions, on_delete=models.DO_NOTHING, unique=False, null=True, blank=True)
    pmt_descx = models.CharField(max_length=200, null=True, blank=True)
    amt_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pay_method = models.ForeignKey(PaymentMethods, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                   null=False, blank=True)
    doc_no = models.CharField(max_length=55, null=True, blank=True)
    bank = models.ForeignKey(Banks, on_delete=models.RESTRICT, related_name='payments', unique=False)
    status = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return str(self.pmt_date) + ' ' + str(self.receipt_no) + ' ' + str(self.invoice_no) + ' ' + str(self.pmt_descx) \
               + ' ' + str(self.amt_paid) + ' ' + str(self.doc_no) + ' ' + str(self.bank)

    class Meta:
        db_table = "apps_Payments"
        ordering = ['school', 'pmt_date', 'receipt_no']
        constraints = [
            models.UniqueConstraint(fields=['school', 'receipt_no', 'invoice_no'], name="unq_school_receipt"),
        ]


class WalletDeposits(models.Model):
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, unique=False, blank=True)
    deposit_id = models.BigIntegerField(blank=True, unique=True, db_index=True)
    accounts = models.OneToOneField('WalletAccounts', on_delete=models.CASCADE, null=True, blank=True)
    pmt_date = models.DateField()
    amt_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pmt_descx = models.CharField(max_length=200, null=True, blank=True)
    pay_method = models.ForeignKey(PaymentMethods, on_delete=models.RESTRICT, related_name='wallets', unique=False,
                                   null=False, blank=True)
    doc_no = models.CharField(max_length=55, null=True, blank=True)
    classroom = models.ForeignKey(ClassRooms, on_delete=models.RESTRICT, related_name='wallets', unique=False,
                                  null=True, blank=True)
    status = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return str(self.id) + ' ' + str(self.student) + ' ' + str(self.pmt_date) + ' ' + str(self.pay_method) \
                + ' ' + str(self.amt_paid)

    class Meta:
        db_table = "apps_WalletDeposits"
        ordering = ['school', 'pmt_date', 'deposit_id']


class WalletAccounts(models.Model):
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, unique=False, related_name='walletaccounts')
    deposit_id = models.BigIntegerField(unique=False, blank=True, null=True)
    withdrawal_id = models.BigIntegerField(unique=False, blank=True, null=True)
    pay_method = models.ForeignKey(PaymentMethods, on_delete=models.RESTRICT, related_name='walletaccounts',
                                   unique=False, null=False, blank=True)
    pmt_date = models.DateField()
    amt_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # run_bal = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    tr_type = models.CharField(max_length=10)

    @property
    def runing(self):  # Calculate Runing Balance for the specified Client
        f1 = Q(school_id=self.school) & Q(student_id=self.student)
        f2 = Q(deposit_id__lte=self.deposit_id)
        bal = WalletAccounts.objects.filter(f1).order_by('pmt_date', 'id').aggregate(balance=Sum('amt_paid', filter=f2))

        if bal is None:
            bal = {'balance': 0.00}
        return bal

    def __str__(self):
        return str(self.pmt_date) + ' ' + str(self.tr_type) + ' ' + str(self.amt_paid) + ' ' +  str(self.runing['balance'])

    class Meta:
        db_table = "apps_WalletAccounts"
        ordering = ['school', 'pmt_date', 'id']


