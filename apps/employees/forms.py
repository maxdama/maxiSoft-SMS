from django import forms
from .models import Employees


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
        exclude = ['school', 'user', 'staff_no']
