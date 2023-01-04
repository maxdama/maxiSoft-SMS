from datetime import date
from django.db import models
from django.db.models import Q, F, Count, Sum
from apps.settings.models import SchoolProfiles, ClassRooms, AcademicSessions
from apps.students.models import Students
from apps.settings import models as sm


# Create your models here.
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
        return str(self.description) + ' ' + str(self.total_fees) + ' ' + str(self.status) + ' ' + str(
            self.inv['counter'])

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
        return str(self.item_no) + ' ' + str(self.item_descx) + ' ' + str(self.qty) + ' ' + str(self.amount)

    class Meta:
        db_table = "apps_FeesPackageDetails"
        ordering = ['school', 'id']


class FinancialTransactions(models.Model):
    trans_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    transaction = models.BigIntegerField(blank=True, primary_key=True)
    descx = models.CharField(max_length=50)
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, related_name='transactions', null=False, blank=True,
                                unique=False)

    def __str__(self):
        return str(self.trans_date) + ' ' + self.descx + ' ' + str(self.transaction)

    class Meta:
        db_table = "apps_FinancialTransactions"
        ordering = ['transaction']
        constraints = [models.UniqueConstraint(fields=['school', 'transaction'], name="unq_school_trans"),]


class Enrollments(models.Model):
    objects = None
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, related_name='enrollment', null=False, blank=True,
                                unique=False)
    school = models.ForeignKey(sm.SchoolProfiles, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    timeline = models.ForeignKey(sm.AcademicTimeLine, on_delete=models.RESTRICT, blank=True, unique=False)
    session = models.ForeignKey(sm.AcademicSessions, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    transaction = models.OneToOneField(FinancialTransactions, on_delete=models.CASCADE, blank=True, related_name='enrollment', null=False)
    reg_no = models.CharField(max_length=50, unique=False, null=False)
    classroom = models.ForeignKey(sm.ClassRooms, on_delete=models.RESTRICT, null=False, blank=True, unique=False)
    trans_date = models.DateField(default=None, null=False, blank=True, db_index=True)
    fee_pkg = models.BigIntegerField(default=0)
    status = models.CharField(max_length=50, null=True, db_index=True)
    first_inv_no = models.BigIntegerField(null=True, blank=True, unique=True, default=None)
    last_rcpt_no = models.CharField(max_length=65, null=True, blank=True, unique=True, default=None)

    @property
    def inv(self):  # Invoice Amount (Cumulative Sum)
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
        # Calculate Total Amount Due of the Student in the current row
        qf1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        qf2 = (Q(invoice__status='np') | Q(invoice__status='pp'))
        # due_amt = Enrollments.objects.filter(qf1).aggregate(due=Sum(F('invoice__balance')-F('invoice__discount'), filter=qf2))
        due_amt = Enrollments.objects.filter(qf1).aggregate(due=Sum(F('invoice__balance'), filter=qf2))
        if due_amt['due'] is None:
            due_amt = {'due': 0.00}
        return due_amt

    @property  # Due Date
    def due(self):
        f1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & (Q(invoice__status='np') | Q(invoice__status='pp')) & Q(timeline_id=self.timeline) & Q(
            session_id=self.session)
        due_dt = Enrollments.objects.filter(f1).values(date=F('invoice__due_date')).order_by('invoice__due_date').first()
        if due_dt is None:
            due_dt = {'date': date.today()}
        return due_dt

    @property
    def last_inv(self):  # Last Invoice Amount
        # Get the Last Invoice Amount issued to Student in Invoice Table
        f1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id=self.timeline) & Q(session_id=self.session)
        last_paid = Enrollments.objects.filter(f1).values(amt=F('invoice__amount')).order_by(
            'invoice__invoice_no').last()
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return

    @property  # Term Cumulative payment
    def term_pmt(self):  # Get the Cumulative payment of the term for the specified Student
        f1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        f2 = Q(payments__session_id=self.session_id) & Q(payments__student_id=self.student_id) & Q(payments__school_id=self.school_id)
        last_paid = Enrollments.objects.filter(f1).aggregate(amt=Sum('payments__amt_paid', filter=f2))
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return last_paid

    @property  # Last Payment Amount
    def last_pmt(self):
        # Get the Last Amount Paid in Payments Table for the specified Student and Class
        f1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        f2 = Q(payments__receipt_no=self.last_rcpt_no) & Q(payments__student_id=self.student_id) & Q(payments__school_id=self.school_id)
        last_paid = Enrollments.objects.filter(f1).aggregate(amt=Sum('payments__amt_paid', filter=f2))
        if last_paid['amt'] is None:
            last_paid = {'amt': 0.00}
        # print(last_paid)
        return last_paid

    @property  # Last Payment Date
    def last_paymt(self):
        # Get the last payment date of every student of the current academic year
        f1 = Q(reg_no=self.reg_no) & Q(school_id=self.school) & Q(timeline_id__lte=self.timeline)
        try:
            last_pmt_dt = Enrollments.objects.filter(f1).values(date=F('payments__pmt_date')).exclude(payments__pmt_date__isnull=True).order_by('payments__pmt_date').last()
            if last_pmt_dt['date'] is None:
                last_pmt_dt = {'date': date.today()}
        except:
            last_pmt_dt = {'date': date.today()}
        return last_pmt_dt

    def __str__(self):
        return str(self.reg_no) + ' ' + str(self.trans_date) + ' ' + str(self.status) + ' ' + str(
            self.tot_amt['due']) + ' ' + str(self.due['date'])

    class Meta:
        db_table = "apps_Enrollments"
        ordering = ['school_id', 'reg_no']
        # unique_together = ('school_id', 'session', 'reg_no', 'classroom')
        constraints = [
            models.UniqueConstraint(fields=['school_id', 'timeline', 'session', 'reg_no'], name="unq_regno_class"),
            models.UniqueConstraint(fields=['school_id', 'timeline', 'session', 'student'], name="unq_stud_class"),
        ]


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
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    disc_perc = models.DecimalField(max_digits=6, decimal_places=1, default=0, null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)
    transaction = models.ForeignKey(FinancialTransactions, on_delete=models.CASCADE, related_name='invoice', blank=True)

    def __str__(self):
        return str(self.invoice_no) + ' ' + str(self.descx) + ' ' + str(self.amount) + ' ' + str(self.status)

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


class FeesPayments(models.Model):
    objects = None
    # pmt_id = models.BigIntegerField(unique=True, primary_key=True)
    receipt_no = models.CharField(max_length=65)
    invoice_no = models.IntegerField(null=True, blank=True)
    pmt_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False)
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, unique=False,  related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                null=True, blank=True)
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                 null=False, blank=True)
    classroom = models.ForeignKey(ClassRooms, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                  null=True, blank=True)
    session = models.ForeignKey(AcademicSessions, on_delete=models.DO_NOTHING, unique=False, null=True, blank=True)
    pmt_descx = models.CharField(max_length=200, null=True, blank=True)
    amt_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pay_method = models.ForeignKey(PaymentMethods, on_delete=models.RESTRICT, related_name='payments', unique=False,
                                   null=False, blank=True)
    instrument_no = models.CharField(max_length=55, null=True, blank=True)
    bank = models.ForeignKey(Banks, on_delete=models.RESTRICT, related_name='payments', unique=False)
    status = models.CharField(max_length=15, null=True, blank=True)
    transaction = models.ForeignKey(FinancialTransactions, on_delete=models.CASCADE,  blank=True, related_name='payments')

    @property
    def runing(self):  # Calculate Runing Balance for the specified Client
        f1 = Q(school_id=self.school_id)  & Q(student_id=self.student_id) # & (Q(doc_type='receipt') | Q(doc_type='invoice'))
        f2 = (Q(doc_no__lte=self.receipt_no) & Q(doc_type='receipt')) | Q(doc_type='invoice')
        bal = FeesAccounts.objects.filter(f1).order_by('trans_date', 'id').aggregate(balance=Sum('amount', filter=f2)-self.invoice.discount)
        if bal is None:
            bal = {'balance': 0.00}
        return bal

    def __str__(self):
        return str(self.pmt_date) + ' ' + str(self.receipt_no) + ' ' + str(self.invoice_no) + ' ' + str(self.pmt_descx) \
               + ' ' + str(self.amt_paid) + ' ' + str(self.instrument_no) + ' ' + str(self.bank)

    class Meta:
        db_table = "apps_FeesPayments"
        ordering = ['school', 'pmt_date', 'receipt_no']
        constraints = [
            models.UniqueConstraint(fields=['school', 'receipt_no', 'invoice_no'], name="unq_school_receipt"),
        ]


class FeesAccounts(models.Model):
    trans_date = models.DateField()
    school = models.ForeignKey(SchoolProfiles, on_delete=models.RESTRICT, unique=False)
    student = models.ForeignKey(Students, on_delete=models.RESTRICT, unique=False)
    enrolled = models.ForeignKey(Enrollments, on_delete=models.RESTRICT, related_name='accounts', unique=False,
                                null=True, blank=True)
    transaction = models.ForeignKey(FinancialTransactions, on_delete=models.CASCADE, blank=True)
    doc_type = models.CharField(max_length=25, null=True, blank=True)
    doc_no = models.BigIntegerField(null=True, blank=True)
    descx = models.CharField(max_length=250)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    run_bal = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    tr_type = models.CharField(max_length=10)

    @property
    def runing(self):  # Calculate Runing Balance for the specified Client
        f1 = Q(school_id=self.school) & Q(student_id=self.student)
        f2 = Q(id__lte=self.id)
        bal = FeesAccounts.objects.filter(f1).order_by('trans_date', 'id').aggregate(balance=Sum('amount', filter=f2))
        if bal is None:
            bal = {'balance': 0.00}
        return bal

    def __str__(self):
        return str(self.trans_date) + ', ' + self.descx + ', ' + str(self.amount) + ', ' \
            + str(self.runing['balance']) + ',  ' + str(self.tr_type) + ', ' + str(self.doc_type) + ', ' + str(self.doc_no)

    class Meta:
        db_table = "apps_FeesAccounts"
        ordering = ['school', 'id']


class WalletPayments(models.Model):
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, unique=False, blank=True)
    payment_id = models.BigIntegerField(blank=True, unique=True, primary_key=True)
    accounts = models.OneToOneField('WalletAccounts', on_delete=models.CASCADE, null=True, blank=True)
    pmt_date = models.DateField()
    amt_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pmt_descx = models.CharField(max_length=200, null=True, blank=True)
    pay_method = models.ForeignKey(PaymentMethods, on_delete=models.RESTRICT, related_name='wallets', unique=False,
                                   null=False, blank=True)
    doc_no = models.CharField(max_length=55, null=True, blank=True)
    classroom = models.ForeignKey(ClassRooms, on_delete=models.RESTRICT, related_name='wallets', unique=False,
                                  null=True, blank=True)
    status = models.CharField(max_length=15, null=True, blank=True)
    transaction = models.ForeignKey(FinancialTransactions, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return str(self.payment_id) + ' ' + str(self.student) + ' ' + str(self.pmt_date) + ' ' + str(self.pay_method) \
               + ' ' + str(self.amt_paid)

    class Meta:
        db_table = "apps_WalletPayments"
        ordering = ['school', 'pmt_date', 'payment_id']


class Wallets(models.Model):
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    student = models.OneToOneField(Students, on_delete=models.CASCADE, unique=True)
    transaction = models.ForeignKey(FinancialTransactions, on_delete=models.CASCADE, blank=True)
    # created = models.DateField(auto_created=True)
    # wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "apps_Wallets"
        ordering = ['school', 'id']

    @property
    def wallet(self):  # Sum the Wallet Balance for the specified Client
        f1 = Q(school_id=self.school) & Q(student_id=self.student)
        bal = WalletAccounts.objects.filter(f1).aggregate(balance=Sum('amt_paid'))
        if bal is None:
            bal = {'balance': 0.00}
        return bal

    @property
    def last_pmt_date(self):  # Get the Accounts last Payment Date for the specified Student
        f1 = Q(school_id=self.school) & Q(student_id=self.student)
        lst_date = WalletAccounts.objects.values('pmt_date').filter(f1).order_by('pmt_date').last()
        if lst_date is None:
            pmt_date = {'pmt_date': date.today()}
        else:
            pmt_date = lst_date
        return pmt_date

    def __str__(self):
        return str(self.student) + ' ' + str(self.wallet['balance']) + ' ' + str(self.last_pmt_date)


class WalletAccounts(models.Model):
    objects = None
    school = models.ForeignKey(SchoolProfiles, on_delete=models.CASCADE, unique=False)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, unique=False, related_name='walletaccounts')
    # payment_id = models.BigIntegerField(unique=False, blank=True, null=True)
    wallet = models.ForeignKey(Wallets, on_delete=models.CASCADE, blank=True, related_name='accounts')
    payment = models.OneToOneField(WalletPayments, on_delete=models.CASCADE, null=True, blank=True)
    withdrawal_id = models.BigIntegerField(unique=False, blank=True, null=True)
    pay_method = models.ForeignKey(PaymentMethods, on_delete=models.RESTRICT, related_name='walletaccounts',
                                   unique=False, null=False, blank=True)
    pmt_date = models.DateField()
    amt_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tr_type = models.CharField(max_length=10)
    transaction = models.ForeignKey(FinancialTransactions, on_delete=models.CASCADE, blank=True)

    @property
    def runing(self):  # Calculate Runing Balance for the specified Client
        f1 = Q(school_id=self.school) & Q(student_id=self.student)
        f2 = Q(payment_id__lte=self.payment_id)
        bal = WalletAccounts.objects.filter(f1).order_by('pmt_date', 'id').aggregate(balance=Sum('amt_paid', filter=f2))

        if bal is None:
            bal = {'balance': 0.00}
        return bal

    def __str__(self):
        return str(self.pmt_date) + ' ' + str(self.tr_type) + ' ' + str(self.amt_paid) + ' ' + str(
            self.runing['balance'])

    class Meta:
        db_table = "apps_WalletAccounts"
        ordering = ['school', 'pmt_date', 'id']
