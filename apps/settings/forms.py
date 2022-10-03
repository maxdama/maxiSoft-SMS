# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
from .models import SchoolProfiles, AcademicTimeLine, AcademicCalender, ClassRooms


class SchoolProfilesForm(forms.ModelForm):
    sch_id = forms.IntegerField(label="School ID",
                                widget=forms.TextInput(
                                    attrs={"class": "form-control form-control-sm", 'readonly': 'True'}
                                )
                                )

    # ---------------------------------------------------------------------------------------
    #  This Code section is to disable sch_id and make it not editable
    def __init__(self, *args, **kwargs):
        super(SchoolProfilesForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['sch_id'].widget.attrs['readonly'] = True

    def clean_sch_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.sch_id
        else:
            return self.cleaned_data['sch_id']

    # ---------------------------------------------------------------------------------------

    rc_no = forms.IntegerField(
        label="RC No:", required=False,
        widget=forms.TextInput(
            attrs={'autofocus': False, "class": "form-control form-control-sm"
                   }
        )
    )

    sch_name = forms.CharField(label="Name of School:", max_length=300,
                               widget=forms.TextInput(
                                   attrs={
                                       'autofocus': True,
                                       "class": "form-control form-control-sm"
                                   }
                               )
                               )

    name_abr = forms.CharField(label="Abbreviation:", max_length=5, required=True,
                               widget=forms.TextInput(
                                   attrs={
                                       'autofocus': False,
                                       "class": "form-control form-control-sm"
                                   }
                               )
                               )

    sch_addr = forms.CharField(label="Address:", max_length=300, required=False,
                               widget=forms.TextInput(
                                   attrs={
                                       'autofocus': False,
                                       "class": "form-control form-control-md"
                                   }
                               )
                               )

    phone_no = forms.CharField(label="Phone No:", max_length=65, required=False,
                               widget=forms.TextInput(
                                   attrs={
                                       'autofocus': False,
                                       "class": "form-control form-control-sm",
                                       "pattern": "[0-9]{11}"
                                   }
                               )
                               )

    start_date = forms.DateField(label='Start Date', input_formats=('%d/%m/%Y',), required=False,
                                 widget=forms.DateInput(format='%d/%m/%Y',
                                                        attrs={'id': 'inputDate', "placeholder": "dd/mm/yyyy",
                                                               'class': 'datepicker form-control form-control-sm'}
                                                        )

                                 )
    email = forms.EmailField(label='E-mail', required=False,
                             widget=forms.DateInput(
                                 attrs={'id': 'email', 'class': 'email form-control form-control-sm'})

                             )

    sch_motor = forms.CharField(label="School Motor:", max_length=300, required=False,
                                widget=forms.TextInput(attrs={"class": "form-control form-control-md"})
                                )

    prop_name = forms.CharField(label="Proprietor:", max_length=80, required=False,
                                widget=forms.TextInput(attrs={"class": "form-control form-control-sm"})
                                )

    no_classrooms = forms.IntegerField(label="Class Room Nos:", required=False,
                                       widget=forms.TextInput(
                                           attrs={'autofocus': False, "class": "form-control form-control-sm"
                                                  }
                                       )
                                       )

    sch_logo = forms.ImageField(label="Logo", required=False,
                                widget=forms.FileInput(
                                    attrs={"class": "btn btn-outline-dark btn-round btn-sm"}
                                )

                                )

    class Meta:
        model = SchoolProfiles
        fields = ('sch_id', 'rc_no', 'sch_name', 'name_abr', 'sch_addr', 'phone_no', 'start_date', 'email', 'prop_name',
                  'sch_motor', 'no_classrooms', 'sch_logo')


class ClassRoomsForm(forms.ModelForm):
    class Meta:
        model = ClassRooms
        fields = '__all__'



class AcademicTimelineForm(forms.ModelForm):
    class Meta:
        model = AcademicTimeLine
        fields = ('sch_id', 'descx', 'st_dt', 'ed_dt', 'status', 's1_starts', 's1_ends', 's2_starts', 's2_ends',
                  's3_starts', 's3_ends')
        exclude = ['status']


    sch_id = forms.IntegerField(label="School ID",
                                widget=forms.TextInput(
                                    attrs={"class": "form-control form-control-sm", 'readonly': 'False', 'hidden': True}
                                )
                                )

    descx = forms.CharField(label="Academic Year:", max_length=30,
                            widget=forms.TextInput(
                                attrs={'name': 'descx', "placeholder": "e.g.  2021/2022", 'autofocus': True,
                                       "class": "form-control form-control-sm"}
                            )
                            )

    st_dt = forms.DateField(label='Start Date', required=False,
                            widget=forms.DateInput(
                                attrs={'id': 'st_id', "placeholder": "dd/mm/yyyy", 'type': 'date', 'required': True,
                                       'autofocus': True, 'class': 'form-control form-control-sm'}
                            )
                            )

    ed_dt = forms.DateField(label='End Date', required=False,
                            widget=forms.DateInput(
                                attrs={'id': 'ed_id', "placeholder": "dd/mm/yyyy", 'type': 'date',
                                       'class': 'datepicker form-control form-control-sm'}
                            )
                            )

"""
        Note: This field is commented out because status is not included in the request.POST that 
        comes from the Form object
        
        status = forms.CharField(label="Status", max_length=30,
                             widget=forms.TextInput(
                                attrs={'autofocus': False, "class": "form-control form-control-sm"}
                            )
                         )
"""


class AcademicCalenderForm(forms.ModelForm):
    class Meta:
        model = AcademicCalender
        fields = ('school', 'timeline', 'acad_yr', 'start_dt', 'end_dt', 'term_id', 'cs_start_dt', 'cs_end_dt',
                  'mb_start_dt', 'mb_end_dt', 'hs_start_dt', 'hs_end_dt', 'status')

    """
    sch_id = forms.IntegerField(label="School ID",
                                widget=forms.TextInput(
                                    attrs={'name': 'sch_id', "class": "form-control form-control-sm", 'readonly': 'False', 'hidden': True}
                                )
                                )
    """
    acad_yr = forms.CharField(label="Description:", max_length=30,
                              widget=forms.TextInput(
                                  attrs={'name': 'acada_yr', "placeholder": "e.g.  2021 / 2022", 'autofocus': False,
                                         "class": "form-control form-control-sm"}
                              )
                              )

    start_dt = forms.DateField(label='Start', required=False,
                               widget=forms.DateInput(
                                   attrs={'name': 'start_id', "placeholder": "dd/mm/yyyy", 'type': 'date',
                                          'class': 'form-control form-control-sm'}
                               )
                               )

    end_dt = forms.DateField(label='Begins', required=False,
                             widget=forms.DateInput(
                                 attrs={'name': 'end_dt', "placeholder": "dd/mm/yyyy", 'type': 'date',
                                        'class': 'form-control form-control-sm'}
                             )
                             )

    term_id = forms.IntegerField(label="School ID",
                                 widget=forms.TextInput(
                                     attrs={"name": 'term_id', "class": "form-control form-control-sm",
                                            'readonly': 'False', 'hidden': True}
                                 )
                                 )

    st_dt_tm1 = forms.DateField(label='Start', required=False,
                               widget=forms.DateInput(
                                   attrs={'name': 'cs_start_dt', "placeholder": "dd/mm/yyyy", 'type': 'date',
                                          'class': 'form-control form-control-sm'}
                               )
                               )
