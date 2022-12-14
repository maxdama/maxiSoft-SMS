# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from . import views as sv
from apps.utils import generate_reg_no


urlpatterns = [
    path('list', sv.student_list, name ='students'),
    # path('new', sv.form_register, name="new_registeration"),
    path('new-registration', sv.new_student_registration, name="new-registeration"),
    path('reg-contx/<int:reg_id>/<int:reg_step>', sv.continue_registration, name="continue"),
    path('update/<int:reg_id>', sv.view_student_for_update, name='view'),
    path('delete/<int:reg_id>', sv.delete_student, name='delete'),
    path('generate/', generate_reg_no, name='gen_reg_no'),
    # path('grab/<int:pkg_id>', sv.invoice_amount, name='get_inv_amt'),

    # path('returning', sv.returned_student_register, name="old_student_register"),

]
