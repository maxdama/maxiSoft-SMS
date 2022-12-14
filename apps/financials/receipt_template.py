import os

from django.db.models import Q, Sum
from django.template.defaultfilters import floatformat
from reportlab.lib.colors import *
from reportlab.lib.units import inch
from datetime import date

from core.settings import BASE_DIR, CORE_DIR


def pdf_receipt_template(c, sch_id, receipt_no):
    stud_name = 'Ajoku Christabel Chibuayim (JSS 2A)'
    wallet_credited = True

    c.translate(inch, inch)
    # logo_path = 'apps/financials/static/assets/img/ngs-logo.
    print('BASE_DIR:')
    p = os.path.join(CORE_DIR, 'apps\\media\\images\\ngscrest.jpg')
    print(p)
    logo_path = "D:\\Projects\\maxiSoft-SMS\\apps\\media\\images\\ngscrest.jpg"
    c.drawImage(logo_path, 5.5 * inch, 8.6*inch, 0.6*inch, 0.5*inch)
    c.setFont("Helvetica", 14)
    c.drawString(0, 9.25 * inch, 'Stepping Stone Secondary School')
    c.setFont("Helvetica", 9)
    c.drawString(0, 9 * inch, '45 Old Aba Road, Port Harcourt, Rivers State')
    c.drawString(0, 8.80 * inch, f"Email: maxdama@gmai.com")
    c.drawString(0, 8.60 * inch, f"Mobile: 081 657 45556")

    # canvas.setLineWidth(width)
    c.setLineWidth(0.1) # Set Line Width for all line except it is change within the code

    c.setStrokeColorRGB(0, 0, 0)  # line colour
    c.line(0.01 * inch, 8.5 * inch, 6.5 * inch, 8.5 * inch)  # horizontal line Header

    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.setFont("Helvetica", 16)
    c.drawString(2.0*inch, 8.22 * inch, 'Receipt')  # Receipt Header
    c.setFont("Helvetica", 9)
    c.drawString(2.80 * inch, 8.26 * inch, 'No:')
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(3.05 * inch, 8.24 * inch, '8440')  # Receipt No

    # Date of Receipt
    c.setFont("Helvetica", 9)
    dt = date.today().strftime('%d-%b-%Y')
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(0.1 * inch, 8.3 * inch, 'Date:')
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(0.55 * inch, 8.3 * inch, dt)

    # Middle Template
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(4.60*inch, 8.25 * inch, 'Due Fees:')
    # c.line(4.61 * inch, 8.21 * inch, 6.5 * inch, 8.21 * inch)  # horizontal line Under Due Balance
    c.drawString(0 * inch, 7.7 * inch, 'Received From:')
    c.line(1.12 * inch, 7.66 * inch, 6.29 * inch, 7.66 * inch)  # horizontal line on Receive from
    c.drawString(4.39 * inch, 7.7 * inch, 'the sum of:')
    # Middle Data
    c.setFont("Times-Roman", 12)
    c.setFillColorRGB(0, 0, 0)  # Black font colour for Receipt
    c.drawRightString(6.25 * inch, 8.25 * inch, '10,000.00')  # Due Balance
    c.drawString(1.15 * inch, 7.7 * inch, stud_name)  # Name of Payer (Student Name)
    c.drawRightString(6.0 * inch, 7.7 * inch, '14,500.00')  # the sum of (Total Amount Received)

    # Table Header
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(0.1 * inch, 7.08 * inch, 'Description')  # Table Header Column 1
    c.drawString(3.0 * inch, 7.08 * inch, 'Fee Amt')  # Table Header Column 2
    c.drawString(3.85 * inch, 7.08 * inch, 'Discount')  # Table Header Column 3
    c.drawString(4.9 * inch, 7.08 * inch, 'Paid')  # Table Header Column 4
    c.drawString(5.74 * inch, 7.08 * inch, 'Fee Bal.')  # Table Header Column 5

    yu = 0.25 # Vertical table line unit
    fl = 7.0 # First Horizontal table Line Start point
    tvp = 7.14  # 'Top Vertical table line point'
    bvp = 6.66  # Bottom Vertical table line point
    # xu = 0.25  # Horizontal table line Unit
    tdp = 6.81  # Table data first point

    c.drawString(0 * inch, 7.4 * inch, 'Payment Details:')
    c.line(0 * inch, fl * inch, 6.27 * inch, fl * inch)  # horizontal line on 1st Payment Details

    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.setFont("Times-Roman", 8)
    # Table Details loop
    for y in range(3):
        if y == 0:
            continue
        elif y > 1:
            bvp = bvp - yu
            tdp = tdp - yu

        print(f'Y = {y}')
        ll = fl - (y * yu)
        c.line(0 * inch, ll * inch, 6.27 * inch, ll * inch)  # horizontal line on 2nd Payment Details

        # Table Details data
        c.drawString(0 * inch, tdp * inch, 'Part Payment: - Admission into JSS 2 - A (2022/2023) 2nd Term')  # Description Column
        c.drawRightString(3.67 * inch, tdp * inch, '250,000.00')  # Amount Column
        c.drawRightString(4.55 * inch, tdp * inch, '0.00')  # Discount Column
        c.drawRightString(5.49 * inch, tdp * inch, '25,000.00')  # Paid Column
        c.drawRightString(6.29 * inch, tdp * inch, '25,000.00')  # Balance Column

    # Table Vertical Lines
    c.line(2.8 * inch, 7.14 * inch, 2.8 * inch, bvp * inch)  # first vertical line Payment Details
    c.line(3.7 * inch, 7.14 * inch, 3.7 * inch, bvp * inch)  # second vertical line Payment Details
    c.line(4.58 * inch, 7.14 * inch, 4.58 * inch, bvp * inch)  # Third vertical line Payment Details
    c.line(5.51 * inch, 7.14 * inch, 5.51 * inch, bvp * inch)  # Forth vertical line Payment Details

    # Bottom Data
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(0 * inch, (bvp - yu) * inch, 'Payment Method:')  # Payment Type
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.setFont("Times-Roman", 10)
    c.drawString(0.9 * inch, (bvp - yu) * inch, 'Bank Teller')  # Payment Type

    if wallet_credited:
        # Draw Rectangle
        # canvas.rect(x, y, width, height, stroke=1, fill=0)
        wallet_amt = 2000
        bvp = (bvp-yu-0.04)
        c.rect(3.58*inch, bvp *inch, inch, 0.3 * inch)
        c.rect(4.58 * inch, bvp * inch, inch, 0.3 * inch)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
        c.drawString(3.61 * inch, (bvp+0.08) * inch, 'Wallet Credit:')  # Payment Type Header
        c.setFont("Times-Roman", 8)
        c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
        c.drawRightString(5.51 * inch, (bvp + 0.08) * inch, f'{wallet_amt:,.2f}')  # Payment Type Header
    else:
        bvp = (bvp-0.18)

    bvp = (bvp-yu-0.02)
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(0 * inch, (bvp-0.06)*inch, 'Printed: ')  # Payment Type Header
    c.setFont("Times-Roman", 10)
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(0 * inch, (bvp-(1.0*yu)) * inch, '25/12/2022')  # Date Printed
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 1)  # Blue font colour for Receipt
    c.drawString(4.9 * inch, bvp * inch, 'Prepared By:')  # Prepared By Header
    c.setFont("Times-Roman", 11)
    c.setFillColorRGB(0, 0, 0)  # Blue font colour for Receipt
    c.drawString(4.9 * inch, (bvp-(0.9*yu)) * inch, 'Maxwell Dama')  # Prepared by


    return c
