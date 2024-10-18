from celery import shared_task
from django.template.loader import render_to_string
from django.conf import settings
import os
from xhtml2pdf import pisa
import psutil

@shared_task
def generate_pdf(servidores, template_path):
    try:
        print("Starting PDF generation...")
        html = render_to_string(template_path, {'servidores': servidores})
        output_path = os.path.join(settings.MEDIA_ROOT, 'relatorio_servidores.pdf')
        with open(output_path, 'wb') as output:
            pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=output)
        if pisa_status.err:
            print("Error creating PDF")
            return 'Erro ao gerar PDF'
        print("PDF created successfully")
        print(f"Memory usage after creating PDF: {psutil.virtual_memory().percent}%")
        return output_path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return 'Erro ao gerar PDF'
