from django import forms
from .models import Students


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = [
            "reg_no", "surname", "first_name", "middle_name", "dob", "stud_pic", "reg_steps", "school"
        ]
        exclude = ['reg_no', 'reg_steps', 'middle_name', 'stud_pic']


class StudentsRegistrationNewForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = [
            "reg_no", "surname", "first_name", "middle_name", "dob",  "gender", "stud_pic", "reg_steps"
        ]
        exclude = ['reg_no', 'reg_steps', 'middle_name']

