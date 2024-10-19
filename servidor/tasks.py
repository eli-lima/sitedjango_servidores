from django.template.loader import render_to_string
import tempfile
import gc
from cloudinary.uploader import upload as cloudinary_upload
from celery import shared_task
from xhtml2pdf import pisa

@shared_task
def generate_pdf(servidores, template_path):
    try:
        print("Starting single PDF generation...")

        # Renderizar o HTML com os dados dos servidores
        try:
            html = render_to_string(template_path, {'servidores': servidores})
            print("HTML renderizado com sucesso para todos os servidores.")
        except Exception as e:
            print(f"Erro ao renderizar o HTML: {e}")
            return {'error': 'Erro ao renderizar HTML'}

        # Criar o PDF em um arquivo temporário
        try:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as output:
                pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=output)
                if pisa_status.err:
                    print("Erro ao criar PDF")
                    return {'error': 'Erro ao gerar PDF'}

                # Carregar o PDF no Cloudinary
                output.flush()  # Garantir que o conteúdo foi escrito corretamente
                output.seek(0)
                response = cloudinary_upload(output.name, resource_type='raw')
                print(f"PDF único enviado para o Cloudinary: {response['url']}")

                # Retornar a URL do PDF no Cloudinary e seu identificador público
                return {
                    'url': response['url'],
                    'public_id': response['public_id']
                }
        except Exception as e:
            print(f"Erro ao gerar ou enviar o PDF: {e}")
            return {'error': 'Erro ao gerar ou enviar o PDF'}

    except Exception as e:
        print(f"Erro geral ao gerar PDF único: {e}")
        return {'error': 'Erro ao gerar PDF único'}
    finally:
        # Limpar a memória após a execução
        gc.collect()
