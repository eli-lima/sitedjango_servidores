from math import ceil
from django.template.loader import render_to_string
import tempfile
import gc
from cloudinary.uploader import upload as cloudinary_upload
from celery import shared_task
from xhtml2pdf import pisa


@shared_task
def generate_pdf(servidores, template_path):
    try:
        print("Starting PDF generation...")

        # Dividir os servidores em lotes de 100 (ou qualquer número adequado)
        batch_size = 100
        total_batches = ceil(len(servidores) / batch_size)
        cloudinary_urls = []

        for batch_num in range(total_batches):
            # Definindo os limites do lote atual
            batch_start = batch_num * batch_size
            batch_end = batch_start + batch_size
            servidores_batch = servidores[batch_start:batch_end]

            # Renderizando o HTML para o lote atual
            html = render_to_string(template_path, {'servidores': servidores_batch})

            # Usando NamedTemporaryFile para criar o PDF temporário
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as output:
                pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=output)
                if pisa_status.err:
                    print(f"Error creating PDF for batch {batch_num}")
                    continue

                # Carregar o PDF no Cloudinary
                output.flush()
                output.seek(0)
                response = cloudinary_upload(output.name, resource_type='raw')
                cloudinary_urls.append(response['url'])

            # Liberar memória ao final de cada lote
            gc.collect()

        print("PDFs uploaded to Cloudinary successfully")
        return cloudinary_urls

    except Exception as e:
        print(f"Error generating PDFs: {e}")
        return 'Erro ao gerar PDFs'
