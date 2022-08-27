from django import forms
from .models import Students, Enrollments


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = [
            "reg_no", "surname", "first_name", "middle_name", "dob", "stud_pic", "reg_steps", "school"
        ]
        exclude = ['reg_no', 'reg_steps', 'middle_name']


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollments
        # fields = [ "student", "school", "timeline", "session", "reg_no", "classroom", "trans_date", "status", "fee_pkg"]
        fields = '__all__'
        exclude = ['status', 'first_inv_no']


