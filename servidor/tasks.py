from celery import shared_task
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import os
from django.conf import settings


@shared_task
def gerar_pdf(context, template_path):
    template = get_template(template_path)
    html = template.render(context)

    output_path = os.path.join(settings.MEDIA_ROOT, 'relatorio_servidores.pdf')
    with open(output_path, 'wb') as output:
        pisa_status = pisa.CreatePDF(html, dest=output)
    if pisa_status.err:
        return 'Erro ao gerar PDF'
    return output_path
