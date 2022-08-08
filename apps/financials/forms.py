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



class FinancialTransactionsForm(forms.ModelForm):
    class Meta:
        model = FinancialTransactions
        fields = '__all__'
        exclude = ['enrolled',  'receipt_no',  'run_bal', 'tr_type']


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'
        exclude = ['package', 'due_date', 'status']