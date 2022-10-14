from django import forms
from django.contrib.auth.models import User

from .models import Employees, Nextofkin


class EmployeeForm(forms.ModelForm):
    '''
    dob = forms.DateField(label='Date of Birth', input_formats=('%d/%m/%Y',), required=False,
                                 widget=forms.DateInput(format='%Y/%m/%d',
                                                        attrs={'id': 'inputDate', "placeholder": "dd/mm/yyyy",
                                                               'class': 'datepicker form-control form-control-sm'}
                                                        )

                                 )
    '''
    class Meta:
        model = Employees
        fields = '__all__'
        exclude = ['school', 'user']


class NextofkinForm(forms.ModelForm):
    class Meta:
        model = Nextofkin
        fields = '__all__'
        exclude = ['employee']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'is_staff', 'is_superuser']
