import os

from django.db.models import Q, Sum
from reportlab.lib.colors import *
from reportlab.lib.units import inch
from datetime import date

from apps.financials.models import FeesPayments, WalletPayments
from apps.settings.models import SchoolProfiles
from core import settings
from core.settings import CORE_DIR


def pdf_receipt_template(c, sch_id, receipt_no):
    s = SchoolProfiles.objects.get(sch_id=sch_id)
    f1 = Q(school_id=sch_id) & Q(receipt_no=receipt_no)
    fees = FeesPayments.objects.filter(f1)

    trans_id = fees.last().transaction_id
    wallet_credited = WalletPayments.objects.filter(transaction_id=trans_id).first()
    wallet_amt = None
    if wallet_credited:
        wallet_amt = wallet_credited.amt_paid

    stud_name = f"{fees.first().student.surname} {fees.first().student.first_name} {fees.first().student.middle_name}"
    stud_class = f"{fees.first().classroom.class_abr}{fees.first().classroom.arm}"

    total = FeesPayments.objects.filter(f1).aggregate(amt_paid=Sum('amt_paid'))
    if total['amt_paid'] is None:
        total = {'amt_paid': 0.00}

    c.translate(inch, inch)
    # logo_path = 'apps/financials/static/assets/img/ngs-logo.jpg'
    logo_path = "D:\\Projects\\maxiSoft-SMS\\apps\\media\\images\\ngscrest.jpg"
    #logo_path = settings.CORE_DIR + "\\apps" + s.sch_logo.url
    logo_path = os.path.join(CORE_DIR, 'apps' + s.sch_logo.url)

    print('Logo Path:')
    print(logo_path)
    # canvas.drawImage(self, image, x, y, width=None, height=None, mask=None)
    c.drawImage(logo_path, 5.5 * inch, 8.6*inch, 0.6*inch, 0.5*inch)
    c.setFont("Helvetica", 14)
    c.drawString(0, 9.25 * inch, s.sch_name)
    c.setFont("Helvetica", 9)
    c.drawString(0, 9 * inch, s.sch_addr)
    c.drawString(0, 8.80 * inch, f"Email: {s.email}")
    c.drawString(0, 8.60 * inch, f"Mobile: {s.phone_no}")

    c.setStrokeColorRGB(0, 0, 0)  # line colour
    c.line(0.01 * inch, 8.5 * inch, 7 * inch, 8.5 * inch)  # horizontal line Header

    c.setFillColorRGB(0, 0, 1)  # font colour
    c.setFont("Times-Bold", 20)
    c.drawString(2.0 * inch, 8.22 * inch, 'Receipt')  # Receipt Header
    c.setFont("Helvetica", 9)
    c.drawString(2.99 * inch, 8.25 * inch, 'No:')
    c.setFont("Helvetica", 11)
    c.drawString(3.25 * inch, 8.25 * inch, fees.first().receipt_no)  # Receipt No

    c.setFillColorRGB(0, 0, 0)  # font colour
    dt = date.today().strftime('%d-%b-%Y')
    c.drawString(0.1 * inch, 8.3 * inch, 'Date:')
    c.drawString(0.55 * inch, 8.3 * inch, fees.first().pmt_date.strftime('%d-%b-%Y'))

    # Middle Template
    c.drawString(4.59 * inch, 8.25 * inch, 'Due Fees:')
    # c.line(4.61 * inch, 8.21 * inch, 6.5 * inch, 8.21 * inch)  # horizontal line Under Due Balance
    c.drawString(0 * inch, 7.7 * inch, 'Received From:')
    c.line(1.12 * inch, 7.66 * inch, 6.20 * inch, 7.66 * inch)  # horizontal line on Receive from
    c.drawString(4.14 * inch, 7.7 * inch, 'the sum of:')
    # Middle Data
    c.setFont("Times-Roman", 12)
    c.drawRightString(6.5 * inch, 8.25 * inch, str(fees.last().runing['balance']))  # Due Balance
    c.drawString(1.15 * inch, 7.7 * inch, f"{stud_name} ({stud_class})")  # Name of Payer (Student Name)
    c.drawRightString(6.2 * inch, 7.7 * inch, str(total['amt_paid']))  # the sum of (Total Amount Received)

    # Table Header
    c.setFont("Helvetica", 8)
    c.drawString(0.1 * inch, 7.08 * inch, 'Description')  # Table Header Column 1
    c.drawString(3.0 * inch, 7.08 * inch, 'Fee Amt')  # Table Header Column 2
    c.drawString(3.85 * inch, 7.08 * inch, 'Discount')  # Table Header Column 3
    c.drawString(4.9 * inch, 7.08 * inch, 'Paid')  # Table Header Column 4
    c.drawString(5.74 * inch, 7.08 * inch, 'Fee Bal.')  # Table Header Column 5

    yu = 0.25  # Vertical table line unit
    fl = 7.0  # First Horizontal table Line Start point
    tvp = 7.14  # 'Top Vertical table line point'
    bvp = 6.66  # Bottom Vertical table line point
    # xu = 0.25  # Horizontal table line Unit
    tdp = 6.81  # Table data first point

    c.drawString(0 * inch, 7.4 * inch, 'Payment Details:')
    c.line(0 * inch, fl * inch, 6.27 * inch, fl * inch)  # horizontal line on 1st Payment Details

    c.setFont("Times-Roman", 8)
    # Table Details loop
    for y, fee in enumerate(fees, start=1):
        if y > 1:
            bvp = bvp - yu
            tdp = tdp - yu

        print(f'Y = {y}')
        ll = fl - (y * yu)
        c.line(0 * inch, ll * inch, 6.27 * inch, ll * inch)  # horizontal line on 2nd Payment Details

        # Table Details data
        c.drawString(0 * inch, tdp * inch, fee.pmt_descx)  # Description Column
        c.drawRightString(3.67 * inch, tdp * inch, str(fee.invoice.amount))  # Fee Amount Column
        c.drawRightString(4.55 * inch, tdp * inch,  str(fee.invoice.discount))  # Discount Column
        c.drawRightString(5.49 * inch, tdp * inch, str(fee.amt_paid))  # Paid Column
        c.drawRightString(6.29 * inch, tdp * inch, str(fee.invoice.balance))  # Balance Column

    # Table Vertical Lines
    c.line(2.8 * inch, 7.14 * inch, 2.8 * inch, bvp * inch)  # first vertical line Payment Details
    c.line(3.7 * inch, 7.14 * inch, 3.7 * inch, bvp * inch)  # second vertical line Payment Details
    c.line(4.58 * inch, 7.14 * inch, 4.58 * inch, bvp * inch)  # Third vertical line Payment Details
    c.line(5.51 * inch, 7.14 * inch, 5.51 * inch, bvp * inch)  # Forth vertical line Payment Details

    # Bottom Data
    c.setFont("Helvetica", 8)
    c.drawString(0 * inch, (bvp - yu) * inch, 'Payment Method:')  # Payment Type
    c.setFont("Times-Roman", 10)
    c.drawString(0.9 * inch, (bvp - yu) * inch, fees.first().pay_method.pay_method)  # Payment Type

    if wallet_credited:
        wallet_amt = wallet_credited.amt_paid

        # Draw Rectangle
        # canvas.rect(x, y, width, height, stroke=1, fill=0)
        bvp = (bvp - yu - 0.04)
        c.rect(3.58 * inch, bvp * inch, inch, 0.3 * inch)
        c.rect(4.58 * inch, bvp * inch, inch, 0.3 * inch)
        c.setFont("Helvetica", 8)
        c.drawString(3.61 * inch, (bvp + 0.08) * inch, 'Wallet Credit:')  # Payment Type Header
        c.setFont("Times-Roman", 10)
        c.drawRightString(5.51 * inch, (bvp + 0.08) * inch, str(wallet_amt))  # Payment Type Header
    else:
        bvp = (bvp - 0.18)

    bvp = (bvp - yu - 0.02)
    c.setFont("Helvetica", 8)
    c.drawString(0 * inch, (bvp - 0.06) * inch, 'Printed: ')  # Payment Type Header
    c.setFont("Times-Roman", 10)
    c.drawString(0 * inch, (bvp - (1.0 * yu)) * inch, '25/12/2022')  # Date Printed
    c.setFont("Helvetica", 8)
    c.drawString(4.9 * inch, bvp * inch, 'Prepared By:')  # Prepared By Header
    c.setFont("Times-Roman", 11)
    c.drawString(4.9 * inch, (bvp - (0.9 * yu)) * inch, 'Maxwell Dama')  # Prepared by

    return c
