from django import forms
from .models import Guardians

class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardians
        fields = ["surname", "other_names", "relationship", "gender", "mobile_no1"]
        exclude = ['relationship']
