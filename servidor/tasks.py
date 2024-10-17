from celery import shared_task
from django.template.loader import render_to_string
from django.conf import settings
import os
from xhtml2pdf import pisa
from PyPDF2 import PdfFileMerger

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
            pisa_status = pisa.CreatePDF(html_chunk, dest=output)
        if pisa_status.err:
            print("Error creating PDF part")
            return 'Erro ao gerar PDF'
        print(f"PDF part {part} created successfully")
        return output_path
    except Exception as e:
        print(f"Error creating PDF part: {e}")
        return 'Erro ao gerar PDF'

@shared_task
def combine_pdfs(parts):
    try:
        from PyPDF2 import PdfFileMerger

        print("Combining PDF parts")
        merger = PdfFileMerger()
        final_output_path = os.path.join(settings.MEDIA_ROOT, 'relatorio_servidores_final.pdf')
        for part in parts:
            merger.append(part)
            print(f"Appended {part} to final PDF")

        with open(final_output_path, 'wb') as output:
            merger.write(output)
        print("Combined PDF created successfully")
        return final_output_path
    except Exception as e:
        print(f"Error combining PDFs: {e}")
        return 'Erro ao combinar PDFs'
