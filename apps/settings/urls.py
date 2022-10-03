
from django.urls import path
from apps.settings import views


urlpatterns = [
    path('school-profile', views.setup_school_profile, name="profile"),
    path('class-rooms', views.setup_class_rooms, name="class-rooms"),
    path('school-terms', views.setup_school_terms, name="school-terms"),
    path('academic-timeline', views.academic_timeline, name="academic-timeline"),
    path('academic-timeline-list', views.list_academic_timeline, name="list-academic-timeline"),
    path('academic-calender', views.setup_academic_calender, name="academic-calender"),
    path('sessions-list', views.list_academic_sessions, name="list-sessions"),
]
