# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from .views import new_guardian, view_guardian_for_update, guardian_list, update_relationship
from apps.guardians import views as gv


urlpatterns = [
    path('list', guardian_list, name ='guardians'),
    path('delete/<int:gad_id>', gv.delete_guardian, name='delete'),
    path('new/<str:oprx_type>', new_guardian, name="new"),
    path('entry/<int:gad_id>/<int:stud_id>/<str:oprx_type>', view_guardian_for_update, name="guardian"),
    path('update_relationship', update_relationship, name='update_relationship')
    # path('enrollment/<int:reg_id>', view_enrollment, name='enrollment')
]

