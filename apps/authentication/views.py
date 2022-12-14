# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm, SignUpForm
from ..decorators import unauthenticated_user
from ..settings.models import SchoolProfiles


@unauthenticated_user
def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None
    prof = {"sch_name": "School Managment Software", "sch_logo": ""}

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                print('User is Authenticated')
                login(request, user)
                sch_id = form.cleaned_data.get("sch_id")
                request.session['school_id'] = sch_id
                request.session['user_name'] = username

                """
                if first_login_today:
                    if end_of_term:
                        ap_do_end_of_term
                """

                return redirect("/")
            else:
                msg = 'Invalid Username or Password'
        else:
            msg = 'Error validating the form'

    else:
        username = ''
        try:
            username = request.COOKIES['last-user']
        except KeyError:
            print('This is your first login')
            pass

        sch_id = 1

        try:
            prof = SchoolProfiles.objects.get(sch_id=sch_id)
        except:
           pass

        form = LoginForm(initial={'username': username, 'sch_id':sch_id})

    return render(request, "accounts/login.html", {"form": form, "msg": msg, "prof": prof})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})
