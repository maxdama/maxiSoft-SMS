from django import forms
from django.contrib.auth.models import User

from .models import Employees, Nextofkin


class EmployeeForm(forms.ModelForm):
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
        fields = ['username', 'password', 'is_staff', 'is_superuser', 'is_active']


class UserFormUpdate(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_staff', 'is_superuser', 'is_active']

