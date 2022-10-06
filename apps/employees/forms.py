from django import forms
from .models import Employees


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employees
        fields = ["title", "surname", "other_names", "gender", "mobile_no"]
        exclude = ['relationship']
