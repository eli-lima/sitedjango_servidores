from celery import shared_task
from django.template.loader import render_to_string
import cloudinary.uploader
import os
from xhtml2pdf import pisa
from PyPDF2 import PdfMerger
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
        output_path = f'relatorio_servidores_{part}.pdf'
        with open(output_path, 'wb') as output:
            pisa_status = pisa.CreatePDF(html_chunk, dest=output)
        if pisa_status.err:
            print("Error creating PDF part")
            return 'Erro ao gerar PDF'
        print(f"PDF part {part} created successfully")
        print(f"Memory usage after creating PDF part {part}: {psutil.virtual_memory().percent}%")
        upload_result = cloudinary.uploader.upload(output_path, resource_type='raw')
        os.remove(output_path)
        return upload_result['url']
    except Exception as e:
        print(f"Error creating PDF part: {e}")
        return 'Erro ao gerar PDF'

@shared_task
def combine_pdfs(part_urls):
    try:
        print("Combining PDF parts")
        merger = PdfMerger()
        final_output_path = 'relatorio_servidores_final.pdf'
        for url in part_urls:
            temp_pdf_path = cloudinary.uploader.download(url, resource_type='raw')
            merger.append(temp_pdf_path)
            os.remove(temp_pdf_path)
            print(f"Appended {url} to final PDF")

        with open(final_output_path, 'wb') as output:
            merger.write(output)
        print("Combined PDF created successfully")
        upload_result = cloudinary.uploader.upload(final_output_path, resource_type='raw')
        os.remove(final_output_path)
        print(f"Memory usage after combining PDFs: {psutil.virtual_memory().percent}%")
        return upload_result['url']
    except Exception as e:
        print(f"Error combining PDFs: {e}")
        return 'Erro ao combinar PDFs'
