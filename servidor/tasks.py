from celery import shared_task
from django.template.loader import render_to_string
from django.conf import settings
import os
from xhtml2pdf import pisa
from PyPDF2 import PdfMerger
import cloudinary.uploader
import psutil


@shared_task
def render_html_chunk(context, template_path, start, end):
    try:
        chunk_context = context[start:end]
        print(f"Rendering HTML chunk: {start} to {end}")
        html = render_to_string(template_path, {'servidores': chunk_context})
        print("HTML chunk rendered successfully")
        return html
    except Exception as e:
        print(f"Error rendering HTML chunk: {e}")
        return 'Erro ao renderizar HTML'


@shared_task
def create_partial_pdf(html_chunk, part):
    try:
        print(f"Creating PDF part: {part}")
        output_path = os.path.join(settings.MEDIA_ROOT, f'relatorio_servidores_{part}.pdf')
        with open(output_path, 'wb') as output:
            pisa_status = pisa.CreatePDF(html_chunk.encode('utf-8'),
                                         dest=output)  # Certifique-se que está codificado corretamente
        if pisa_status.err:
            print("Error creating PDF part")
            return 'Erro ao gerar PDF'
        print(f"PDF part {part} created successfully")
        print(f"Memory usage after creating PDF part {part}: {psutil.virtual_memory().percent}%")

        # Upload para Cloudinary
        cloudinary_response = cloudinary.uploader.upload(output_path)
        cloudinary_url = cloudinary_response['secure_url']
        return cloudinary_url
    except Exception as e:
        print(f"Error creating PDF part: {e}")
        return 'Erro ao gerar PDF'


@shared_task
def combine_pdfs(parts):
    try:
        print("Combining PDF parts")
        merger = PdfMerger()
        final_output_path = os.path.join(settings.MEDIA_ROOT, 'relatorio_servidores_final.pdf')
        for part in parts:
            merger.append(part)
            print(f"Appended {part} to final PDF")

        with open(final_output_path, 'wb') as output:
            merger.write(output)
        print("Combined PDF created successfully")
        print(f"Memory usage after combining PDFs: {psutil.virtual_memory().percent}%")

        # Upload final PDF para Cloudinary
        cloudinary_response = cloudinary.uploader.upload(final_output_path)
        cloudinary_url = cloudinary_response['secure_url']
        return cloudinary_url
    except Exception as e:
        print(f"Error combining PDFs: {e}")
        return 'Erro ao combinar PDFs'
