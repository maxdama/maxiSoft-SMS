import os

from django.db.models import Q, Sum
from reportlab.lib.colors import *
from reportlab.lib.units import inch
from datetime import date

from apps.employees.models import Employees
from apps.financials.models import FeesPayments, WalletPayments
from apps.settings.models import SchoolProfiles
# from core import settings
from core.settings import CORE_DIR


def pdf_receipt_template(request, c, sch, receipt_no):
    dt_today = date.today().strftime('%d-%b-%Y')

    sch_id = sch.sch_id
    f1 = Q(school_id=sch_id) & Q(receipt_no=receipt_no)
    fees = FeesPayments.objects.filter(f1).order_by('invoice_no')

    trans_id = fees.last().transaction_id
    wallet_credited = WalletPayments.objects.filter(transaction_id=trans_id).first()
    wallet_amt = 0
    if wallet_credited:
        wallet_amt = wallet_credited.amt_paid

    stud_name = f"{fees.first().student.surname} {fees.first().student.first_name} {fees.first().student.middle_name}"
    stud_class = f"{fees.first().classroom.class_abr}{fees.first().classroom.arm}"

    total = FeesPayments.objects.filter(f1).aggregate(amt_paid=Sum('amt_paid'))
    if total['amt_paid'] is None:
        total = {'amt_paid': 0.00}

    tot_amt_paid = total['amt_paid'] + wallet_amt

    c.translate(inch, inch)
    # logo_path = settings.CORE_DIR + "\\apps" + s.sch_logo.url
    logo_path = os.path.join(CORE_DIR, 'apps' + sch.sch_logo.url) # Absolute Path

    print('Logo Path:')
    print(logo_path)
    # canvas.drawImage(self, image, x, y, width=None, height=None, mask=None)
    c.drawImage(logo_path, 5.5 * inch, 8.6*inch, 0.6*inch, 0.5*inch)
    c.setFont("Helvetica", 14)
    c.drawString(0, 9.25 * inch, sch.sch_name)
    c.setFont("Helvetica", 9)
    c.drawString(0, 9*inch, sch.sch_addr)
    c.drawString(0, 8.80 * inch, f"Email: {sch.email}")
    c.drawString(0, 8.60 * inch, f"Mobile: {sch.phone_no}")

    c.setStrokeColorRGB(0, 0, 0)  # line colour
    c.setLineWidth(0.1)  # Set Line Width for all line except it is change within the code
    c.line(0.01 * inch, 8.5 * inch, 6.5*inch, 8.5*inch)  # horizontal line Header

    c.setFillColorRGB(0, 0, 1)  # font colour
    c.setFont("Helvetica", 16)
    c.drawString(2.0*inch, 8.22 * inch, 'Receipt')  # Receipt Header
    c.setFont("Helvetica", 9)
    c.drawString(2.80 * inch, 8.26 * inch, 'No:')
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(3.05 * inch, 8.24 * inch, fees.first().receipt_no)  # Receipt No

    # Date of Receipt
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    dt = date.today().strftime('%d-%b-%Y')
    c.drawString(0.1 * inch, 8.3 * inch, 'Date:')
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(0.55 * inch, 8.3 * inch, fees.first().pmt_date.strftime('%d-%b-%Y'))

    # Middle Template
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(4.60 * inch, 8.25 * inch, 'Due Fees:')
    c.drawString(0 * inch, 7.7 * inch, 'Fee Payment For:')
    c.line(1.12 * inch, 7.66 * inch, 6.29 * inch, 7.66 * inch)  # horizontal line on Receive from
    c.drawString(4.39 * inch, 7.7 * inch, 'Amount Paid:')
    # Middle Data
    c.setFont("Times-Roman", 12)
    c.setFillColorRGB(0, 0, 0)  # Black font colour for Receipt
    c.drawString(1.15 * inch, 7.7 * inch, f"{stud_name} ({stud_class})")  # Name of Payer (Student Name)
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.1, 0.75, 0.02)  # Green font colour for Receipt
    c.drawRightString(6.1 * inch, 7.7 * inch, f'{tot_amt_paid:,.2f}')  # the sum of (Total Amount Paid)
    c.setFillColorRGB(1, 0, 0)  # Red font colour for Receipt
    if fees.last().runing['balance'] == 0:
        c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawRightString(6.25 * inch, 8.25 * inch, f"{fees.last().runing['balance']:,.2f}")  # Due Fees

    # Table Header
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(0.3 * inch, 7.08 * inch, 'Description')  # Table Header Column 1
    c.drawString(3.0 * inch, 7.08 * inch, 'Fee Amt')  # Table Header Column 2
    c.drawString(3.89 * inch, 7.08 * inch, 'Discount')  # Table Header Column 3
    c.drawString(4.83 * inch, 7.08 * inch, 'Fee Paid')  # Table Header Column 4
    c.drawString(5.74 * inch, 7.08 * inch, 'Fee Bal.')  # Table Header Column 5

    yu = 0.25  # Vertical table line unit
    fl = 7.0  # First Horizontal table Line Start point
    tvp = 7.14  # 'Top Vertical table line point'
    bvp = 6.66  # Bottom Vertical table line point
    # xu = 0.25  # Horizontal table line Unit
    tdp = 6.81  # Table data first point

    # Method Rectangler Box
    c.rect(4.35 * inch, (bvp + 0.7) * inch, 1.94*inch, 0.3 * inch, fill=0)  # (x,y, width, hight, fill=1)

    c.drawString(4.39 * inch, 7.47 * inch, 'Method:')
    c.setFillColorRGB(0, 0, 0)  # Black font colour for Receipt
    c.setFont("Times-Roman", 9.8)
    c.drawString(5.05 * inch, 7.47 * inch, fees.first().pay_method.pay_method)  # Payment Type
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.setFont("Times-Italic", 9.8)
    c.drawString(0 * inch, 7.27 * inch, 'Payment Details:')
    c.line(0 * inch, fl * inch, 6.27 * inch, fl * inch)  # horizontal line on 1st Payment Details

    c.setFillColorRGB(0, 0, 0)  # Black font colour for Receipt
    # Table Details loop
    for y, fee in enumerate(fees, start=1):
        if y > 1:
            bvp = bvp - yu
            tdp = tdp - yu

        print(f'Y = {y}')
        ll = fl - (y * yu)
        c.line(0 * inch, ll * inch, 6.27 * inch, ll * inch)  # horizontal line on 2nd Payment Details

        # Table Details data
        c.setFont("Times-Roman", 8)
        c.drawString(0 * inch, tdp * inch, fee.pmt_descx)  # Description Column
        c.setFont("Helvetica", 8)
        c.drawRightString(3.67 * inch, tdp * inch, f"{fee.invoice.amount:,.2f}")  # Fee Amount Column f'{wallet_amt:,.2f}'
        c.drawRightString(4.55 * inch, tdp * inch, f"{fee.invoice.discount:,.2f}")  # Discount Column
        c.drawRightString(5.49 * inch, tdp * inch, f"{fee.amt_paid:,.2f}")  # Paid Column
        if fee.runing['balance'] > 0:
            c.setFillColorRGB(1, 0, 0)  # Red font colour for Receipt
        c.drawRightString(6.29 * inch, tdp * inch, f"{fee.runing['balance']:,.2f}")  # Balance Column

    # Table Vertical Lines
    c.line(2.8 * inch, 7.14 * inch, 2.8 * inch, bvp * inch)  # first vertical line Payment Details
    c.line(3.7 * inch, 7.14 * inch, 3.7 * inch, bvp * inch)  # second vertical line Payment Details
    c.line(4.58 * inch, 7.14 * inch, 4.58 * inch, bvp * inch)  # Third vertical line Payment Details
    c.line(5.51 * inch, 7.14 * inch, 5.51 * inch, bvp * inch)  # Forth vertical line Payment Details

    # Bottom Data
    # c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt

    stud_id = fees.first().student_id
    # Get the distinct invoice_no in FeesPayment for the specified receipt No
    inv_nos = FeesPayments.objects.filter(f1).values('invoice_no').order_by("invoice_no").distinct()
    # Get the Previous Total Payments for the specified invoice no excluding the current receipt no
    f3 = Q(school_id=sch_id) & Q(student_id=stud_id) & Q(invoice_no__in=inv_nos) & Q(receipt_no__lt=receipt_no)
    prv_fee = FeesPayments.objects.filter(f3).order_by('receipt_no').aggregate(fees_paid=Sum('amt_paid'))

    bvp = (bvp - (yu-0.05))
    c.drawString(3.60 * inch, bvp  * inch, 'Previous Payments:')  # Payment Type
    c.setFillColorRGB(0, 0, 0)  # Black font colour for Receipt
    # c.setFont("Times-Roman", 10)

    if prv_fee['fees_paid'] is None:
        prev_fee = 0
    else:
        prev_fee = prv_fee['fees_paid']
    c.drawRightString(5.49 * inch, bvp * inch,  f"{prev_fee:,.2f}")  # Previous Payments

    if wallet_credited:
        wallet_amt = wallet_credited.amt_paid
        # Draw Rectangle
        # canvas.rect(x, y, width, height, stroke=1, fill=0)
        bvp = (bvp - yu - 0.15)
        c.rect(3.58 * inch, bvp * inch, inch, 0.3 * inch)
        c.rect(4.58 * inch, bvp * inch, inch, 0.3 * inch)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
        c.drawString(3.91 * inch, (bvp + 0.08) * inch, 'Wallet Credit:')  # Payment Type Header
        # c.setFont("Times-Roman", 8)
        c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
        c.drawRightString(5.49*inch, (bvp + 0.08)*inch, f'{wallet_amt:,.2f}')  # Payment Type Header
        # f'{my_float:,.2f}'
    else:
        bvp = (bvp-0.18) # Push some items a little down

    bvp = bvp -yu
    c.line(0.01 * inch, (bvp-0.20) * inch, 6.5 * inch, (bvp-0.20) * inch)  # botoom horizontal line

    bvp = (bvp - yu - 0.02)
    c.setFont("Helvetica", 8)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(0 * inch, (bvp - 0.06) * inch, 'Date Printed: ')  # Payment Type Header

    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(0 * inch, (bvp-(0.8*yu)) * inch, dt_today)  # Date Printed
    bvp = (bvp - 0.05)
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt

    if request.user.id:
        emp_name = Employees.objects.filter(user_id=request.user.id).values('other_names', 'surname').first()
        if emp_name:
            prepared_by = emp_name['other_names'] + ' ' + emp_name['surname']
        else:
            prepared_by = 'Administrator'

        c.drawString(4.9 * inch, bvp * inch, 'Prepared By:')  # Prepared By Header
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
        c.drawString(4.9 * inch, (bvp - (0.9 * yu)) * inch, prepared_by)  # Prepared by

    return c
