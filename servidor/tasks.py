from celery import shared_task
from django.template.loader import render_to_string
import os
from xhtml2pdf import pisa
from cloudinary.uploader import upload as cloudinary_upload
import gc  # Para liberar a memória manualmente após o processamento
import tempfile  # Para a criação de arquivos temporários


@shared_task
def generate_pdf(servidores, template_path):
    try:
        print("Starting PDF generation...")
        html = render_to_string(template_path, {'servidores': servidores})

        # Usando NamedTemporaryFile para evitar criação de arquivos permanentes e gerenciar melhor o espaço em memória
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as output:
            pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=output)
            if pisa_status.err:
                print("Error creating PDF")
                return 'Erro ao gerar PDF'

            output.flush()  # Garante que todo conteúdo seja escrito
            output.seek(0)  # Vai para o início do arquivo para fazer o upload

            # Upload do PDF para o Cloudinary
            response = cloudinary_upload(output.name, resource_type='raw')
            cloudinary_url = response['url']

        # Força o garbage collector para liberar memória
        gc.collect()

        print("PDF uploaded to Cloudinary successfully")
        return cloudinary_url

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return 'Erro ao gerar PDF'
