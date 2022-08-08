from django.urls import path # Importing part which will be used to map to the URLs
from . import views   # Importing views (Business logic) that will handle the connections


urlpatterns = [
    path('package-list', views.financial_package_list, name='packages'),
    path('new-package', views.new_package, name='new-package'),
    path('delete-package/<int:pkg_id>', views.delete_package, name='delete-package'),
    path('edit-package/<int:pkg_id>', views.edit_package, name='edit-package'),
    path('new-enrollment/<int:reg_id>', views.new_student_enrollment, name='new-enrollment'),
    path('enrollment-list', views.list_enrollments, name='list-enrollments'),
    path('cancel-enrollment/<int:enr_id>/<int:inv_no>', views.cancel_enrollment, name='cancel-enrollment'),
    path('update-enrollment/<int:enr_id>/<int:inv_no>', views.update_enrollment, name='update-enrollment'),

]
