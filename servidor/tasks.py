from celery import shared_task
from django.template.loader import render_to_string
from cloudinary.uploader import upload as cloudinary_upload
import os
import requests
from xhtml2pdf import pisa
from PyPDF2 import PdfMerger
import psutil


@shared_task
def render_html_chunk(servidores_chunk, template_path):
    try:
        print(f"Rendering HTML chunk for servidores: {servidores_chunk}")
        html = render_to_string(template_path, {'servidores': servidores_chunk})
        print("HTML chunk rendered successfully")
        return html
    except Exception as e:
        print(f"Error rendering HTML chunk: {e}")
        return 'Erro ao renderizar HTML'


@shared_task
def create_partial_pdf(html_chunk, part):
    try:
        if isinstance(html_chunk, dict):
            html_chunk = str(html_chunk)  # Converte dict para string
        print(f"Creating PDF part: {part}")
        output_path = os.path.join('/tmp', f'relatorio_servidores_{part}.pdf')
        with open(output_path, 'wb') as output:
            pisa_status = pisa.CreatePDF(html_chunk.encode('utf-8'), dest=output)
        if pisa_status.err:
            print("Error creating PDF part")
            return 'Erro ao gerar PDF'
        print(f"PDF part {part} created successfully")
        print(f"Memory usage after creating PDF part {part}: {psutil.virtual_memory().percent}%")

        # Upload do PDF para o Cloudinary
        response = cloudinary_upload(output_path, resource_type='raw')
        cloudinary_url = response['url']

        # Deletar o arquivo temporário
        os.remove(output_path)

        return cloudinary_url
    except Exception as e:
        print(f"Error creating PDF part: {e}")
        return 'Erro ao gerar PDF'


@shared_task
def combine_pdfs(parts):
    try:
        print("Combining PDF parts")
        merger = PdfMerger()
        final_output_path = os.path.join('/tmp', 'relatorio_servidores_final.pdf')
        for part in parts:
            if part.startswith('http'):
                print(f"Downloading and appending {part} to final PDF")
                response = requests.get(part)
                part_path = os.path.join('/tmp', os.path.basename(part))
                with open(part_path, 'wb') as f:
                    f.write(response.content)
                merger.append(part_path)
            else:
                print(f"Appending {part} to final PDF")
                merger.append(part)

        with open(final_output_path, 'wb') as output:
            merger.write(output)
        print("Combined PDF created successfully")

        # Upload do PDF final para o Cloudinary
        response = cloudinary_upload(final_output_path, resource_type='raw')
        cloudinary_final_url = response['url']

        # Deletar o arquivo temporário
        os.remove(final_output_path)

        print(f"Memory usage after combining PDFs: {psutil.virtual_memory().percent}%")
        return cloudinary_final_url
    except Exception as e:
        print(f"Error combining PDFs: {e}")
        return 'Erro ao combinar PDFs'
