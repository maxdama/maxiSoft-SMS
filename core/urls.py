# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this

# Added this when working on Image
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    path('admin/', admin.site.urls),          # Django admin route
    path('settings/', include('apps.settings.urls')),
    path('financials/', include('apps.financials.urls')),

    path('students/', include("apps.students.urls")),
    path('guardians/', include("apps.guardians.urls")),
    path("", include("apps.authentication.urls")), # Auth routes - login / register
    path("", include("apps.home.urls"))            # UI Kits Html files

]
# if settings.DEBUG:
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)