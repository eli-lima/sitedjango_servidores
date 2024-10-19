from django.template.loader import render_to_string
import tempfile
import gc
from cloudinary.uploader import upload as cloudinary_upload
from xhtml2pdf import pisa
from cloudinary.api import resources, delete_resources
from celery import shared_task
from datetime import datetime, timedelta


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
            return 'Erro ao renderizar HTML'

        # Criar o PDF em um arquivo temporário
        try:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as output:
                pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=output)
                if pisa_status.err:
                    print("Erro ao criar PDF")
                    return 'Erro ao gerar PDF'

                # Carregar o PDF no Cloudinary
                output.flush()  # Garantir que o conteúdo foi escrito corretamente
                output.seek(0)
                response = cloudinary_upload(output.name, resource_type='raw',
                                             folder="media/relatorios_pdfs")  # Definir a pasta onde o arquivo será salvo
                print(f"PDF único enviado para o Cloudinary: {response['url']}")

                # Retornar a URL do PDF no Cloudinary
                return response['url']
        except Exception as e:
            print(f"Erro ao gerar ou enviar o PDF: {e}")
            return 'Erro ao gerar ou enviar o PDF'

    except Exception as e:
        print(f"Erro geral ao gerar PDF único: {e}")
        return 'Erro ao gerar PDF único'
    finally:
        # Limpar a memória após a execução
        gc.collect()


# Tarefa para deletar PDFs com mais de 3 meses
@shared_task
def delete_old_pdfs():
    print("Iniciando a exclusão de PDFs antigos...")

    try:
        # Calcular a data limite (3 meses atrás)
        cutoff_date = datetime.now() - timedelta(days=90)

        # Listar todos os PDFs na pasta "relatorios_pdfs"
        result = resources(type="upload", prefix="relatorios_pdfs", resource_type="raw")

        # Verificar cada PDF e deletar os que têm mais de 3 meses
        for pdf in result.get('resources', []):
            # Converter a data de criação do PDF
            created_at = datetime.strptime(pdf['created_at'], '%Y-%m-%dT%H:%M:%SZ')

            if created_at < cutoff_date:
                # Deletar o PDF se tiver mais de 3 meses
                delete_resources([pdf['public_id']], resource_type="raw")
                print(f"PDF deletado: {pdf['public_id']}")

        print("Exclusão de PDFs antigos concluída.")
    except Exception as e:
        print(f"Erro ao excluir PDFs antigos: {e}")


from celery import shared_task

@shared_task
def test_celery():
    print("Celery is working!")