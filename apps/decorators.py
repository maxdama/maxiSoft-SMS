from django.contrib import messages
from django.shortcuts import redirect


def unauthenticated_user(view_funct):
    """
        This decorator prevents user that is already login to call the login page again.
        If the user is already login it redirects the user to the home page
    """
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return view_funct(request, *args, **kwargs)

    return wrapper_func


decorator_with_arguments = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs)


@decorator_with_arguments
def custom_permission_required(function, perm):
    """Decorator for views that checks whether a user is given a particular permission """
    def _function(request, *args, **kwargs):
        if request.user.has_perm(perm):
            return function(request, *args, **kwargs)
        else:
            p = perm.split(".")[1]
            if p:
                msg = 'You are NOT permitted to ' + p
            else:
                msg = "You are NOT permitted to carry out this action"
            messages.error(request, msg)
            # Going back to previous URL
            return redirect(request.META['HTTP_REFERER'])

    return _function
