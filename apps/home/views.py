# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse

from apps.students.models import Students


def students_statistics(sch_id):
    tot_student = Students.objects.filter(school_id=sch_id).count()
    tot_pending = Students.objects.filter(school_id=sch_id, reg_status='pending').count()
    tot_enrolled = Students.objects.filter(school_id=sch_id, reg_status='enrolled').count()
    tot_active = Students.objects.filter(school_id=sch_id, reg_status='active').count()

    reg_statistics = {'tot_pending': tot_pending, 'tot_student': tot_student, 'tot_enrolled': tot_enrolled, 'tot_active': tot_active}
    return reg_statistics


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}
    context = {}

    if request.session.has_key('user_name'):
        username = request.session['user_name']
        sch_id = request.session['school_id']
    else:
        username = request.POST.get('username')

    # html_template = loader.get_template('home/index.html')
    # return HttpResponse(html_template.render(context, request))

    stud_stat = students_statistics(sch_id)
    print(stud_stat)
    context = {'stud': stud_stat}

    days_expire = 30
    max_age = days_expire * 24 * 60 * 60
    response = render(request, 'dashboard1.html', context)
    response.set_cookie('last-user', username, max_age=max_age)  # Set the cookies

    return response


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))
