from django.contrib.auth import logout
from django.shortcuts import redirect
import shutil
import os.path
from os import path


def get_school_id(request):
    sch_id = 0
    if request.session.has_key('school_id'):
        sch_id = request.session['school_id']
        return sch_id
    else:
        logout(request)
        return redirect("logout")


def default_image_restore(request):
    """ if the default picture file is not found in the static folder
        the function copy it from the images folder to the static folder.
        It ensures that the default student picture file is always in the
        static folder even if it is delete in the course of
        deleting a student record.
    """
    src_dir = "apps/media/images/"
    dst_dir = "apps/media/images/static"
    # files = [src_dir + 'default.png', src_dir + 'file2.txt', src_dir + 'file3.txt']
    files = [src_dir + 'default.png']

    if not path.exists(dst_dir + "/default.png"):
        for f in files:
            shutil.copy(f, dst_dir)

    return None