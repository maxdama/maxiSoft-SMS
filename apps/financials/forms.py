from django import forms

from apps.financials.models import *


class FeesPackageForm(forms.ModelForm):
    class Meta:
        model = FeesPackage
        fields = '__all__'


class FeesPackageDetailsForm(forms.ModelForm):
    class Meta:
        model = FeesPackageDetails
        fields = '__all__'
        exclude = ['package']

"""
class FinancialTransactionsForm(forms.ModelForm):
    class Meta:
        model = FinancialTransactions
        fields = '__all__'
        exclude = ['enrolled', 'receipt_no', 'run_bal', 'tr_type', 'amount']
"""


class FeesAccountsForm(forms.ModelForm):
    class Meta:
        model = FeesAccounts
        fields = '__all__'
        exclude = ['receipt_no', 'run_bal', 'tr_type', 'amount', 'trans_date', 'descx']


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'
        exclude = ['package', 'due_date', 'balance', 'status', 'amount']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payments
        fields = '__all__'
        exclude = ['receipt_no', 'invoice_no', 'amt_paid', 'pmt_descx', 'status']


class WalletAccountsForm(forms.ModelForm):
    class Meta:
        model = WalletAccounts
        fields = '__all__'
        exclude = ['doc_type', 'doc_no', 'amt_paid', 'status', 'run_bal', 'tr_type']


class WalletPaymentForm(forms.ModelForm):
    class Meta:
        model = WalletPayments
        fields = '__all__'
        exclude = ['amt_paid', 'status', 'balance', 'payment_id']
