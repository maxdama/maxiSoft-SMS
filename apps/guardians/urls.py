# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from .views import new_guardian, view_guardian, guardian_list
from apps.guardians import views as gv


urlpatterns = [
    path('list', guardian_list, name ='guardians'),
    path('delete/<int:gad_id>', gv.delete_guardian, name='delete'),
    path('new', new_guardian, name="new"),
    path('update/<int:gad_id>/<int:reg_id>', view_guardian, name="guardian"),
    # path('enrollment/<int:reg_id>', view_enrollment, name='enrollment')
]

