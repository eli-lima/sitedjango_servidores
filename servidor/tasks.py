from celery import shared_task
from django.template.loader import get_template
from django.core.files.base import ContentFile
from django.conf import settings
from xhtml2pdf import pisa
import os


@shared_task
def gerar_pdf(context, template_path):
    template = get_template(template_path)
    html = template.render(context)
    output = ContentFile('')

    pisa_status = pisa.CreatePDF(html, dest=output)

    if pisa_status.err:
        return 'Erro ao gerar PDF'

    output_path = os.path.join(settings.MEDIA_ROOT, 'relatorio_servidores.pdf')
    with open(output_path, 'wb') as f:
        f.write(output.read())

    return output_path
