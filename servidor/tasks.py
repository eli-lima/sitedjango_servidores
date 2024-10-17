from celery import shared_task
from django.template.loader import get_template
from django.core.files.base import ContentFile
import os
from django.conf import settings
from xhtml2pdf import pisa

@shared_task
def render_html(context, template_path):
    template = get_template(template_path)
    html = template.render(context)
    return html

@shared_task
def create_pdf(html):
    output_path = os.path.join(settings.MEDIA_ROOT, 'relatorio_servidores.pdf')
    with open(output_path, 'wb') as output:
        pisa_status = pisa.CreatePDF(html, dest=output)
    if pisa_status.err:
        return 'Erro ao gerar PDF'
    return output_path
