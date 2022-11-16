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
            return view_funct(request, *args,**kwargs)

    return wrapper_func