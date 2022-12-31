from django.urls import path # Importing part which will be used to map to the URLs
from . import views   # Importing views (Business logic) that will handle the connections


urlpatterns = [
    path('package-list', views.financial_package_list, name='packages'),
    path('new-package', views.new_package, name='new-package'),
    path('delete-package/<int:pkg_id>', views.delete_package, name='delete-package'),
    path('edit-package/<int:pkg_id>', views.edit_package, name='edit-package'),
    path('get-invoice-amount/<int:pkg_id>', views.invoice_amount, name='get_inv_amt'),
    path('new-enrollment/<int:reg_id>', views.new_student_enrollment, name='new-enrollment'),
    path('student-enrolled-list', views.list_enrollments, name='list-enrollments'),
    path('cancel-enrollment/<int:enr_id>/<int:inv_no>/<int:trans_id>', views.cancel_enrollment, name='cancel-enrollment'),
    path('student-enrolled-update/<int:enr_id>/<int:inv_no>', views.student_enrolled_update, name='update-enrollment'),
    path('student-re-enrollment/<int:stud_id>', views.student_re_enrollment, name="re-enrollment"),
    path('student-payment/<int:stud_id>', views.student_payment, name='payment-entry'),
    path('wallet-account/<int:stud_id>', views.wallet_account, name='wallet_account'),
    path('cancel-transaction/<int:sch_id>/<int:trans_id>', views.cancel_financial_transaction, name='cancel-transaction'),
    # path('payment-receipt/<int:sch_id>/<int:receipt_id>/<str:action>', views.payment_receipt, name='payment-receipt'),
    path('print-receipt/<int:sch_id>/<int:stud_id>/<int:receipt_no>', views.print_pdf_receipt, name='print-receipt'),
    path('payment-receipt-preview/<int:sch_id>/<int:receipt_no>', views.preview_payments, name='preview-payment'),

]
