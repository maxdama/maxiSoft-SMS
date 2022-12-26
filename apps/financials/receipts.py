from django.http import FileResponse
from reportlab.pdfgen import canvas

#from apps.pdf_templates import pdf_receipt_template
from receipt_template import pdf_receipt_template

my_path = 'd:\\py2pdf\\ngs_receipt.pdf'
from reportlab.lib.pagesizes import letter

# from apps.pdf_templates import pdf_receipt_template

c = canvas.Canvas(my_path,pagesize=letter)
c = pdf_receipt_template(c, 1, 1) # run the template

c.showPage()
c.save()

FileResponse(open(my_path, 'rb'), as_attachment=False, content_type='application/pdf')