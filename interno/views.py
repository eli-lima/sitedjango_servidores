
from .forms import UploadExcelInternosForm

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, UpdateView
from django.db.models import Q

import os
import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.core.files.storage import default_storage
from .models import Interno, PopulacaoCarceraria
from .forms import PopulacaoCarcerariaForm
import face_recognition
import json
import base64
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.forms.models import model_to_dict
from io import BytesIO
from PIL import Image
import numpy as np

#modulo facial


def detalhes_interno(request, interno_id):
    # Obtém o interno ou retorna 404
    interno = get_object_or_404(Interno, id=interno_id)

    # Verifica se é uma requisição AJAX/API
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Prepara os dados para resposta JSON
        data = model_to_dict(interno, exclude=['foto'])  # Exclui o campo foto binário

        # Adiciona campos extras
        data.update({
            'unidade': str(interno.unidade) if interno.unidade else None,
            'foto_url': interno.foto.url if interno.foto else '/static/images/default-profile.png',
            'detalhes_url': f'/interno/{interno.id}/detalhes/'
        })

        # Adicione quaisquer outros campos que precise na API
        if hasattr(interno, 'data_nascimento'):
            data['data_nascimento'] = interno.data_nascimento.strftime('%d/%m/%Y') if interno.data_nascimento else None

        return JsonResponse(data)

    # Se não for AJAX, renderiza o template normal
    context = {
        'interno': interno,
        'foto_url': interno.foto.url if interno.foto else '/static/images/default-profile.png'
    }
    return render(request, 'detalhes_interno.html', context)


@csrf_exempt
def cadastrar_rosto(request, interno_id):
    from PIL import Image
    import io
    import numpy as np
    import face_recognition
    from django.core.files.base import ContentFile

    interno = get_object_or_404(Interno, id=interno_id)

    print(f"\n=== INÍCIO DO PROCESSAMENTO ===")
    print(f"Registrando rosto para o interno: {interno.nome} (ID: {interno_id})")

    if request.method == 'POST':
        fonte_imagem = request.POST.get('fonte_imagem')
        print(f"Fonte da imagem: {fonte_imagem}")

        try:
            if fonte_imagem == 'camera':
                print("Processando imagem da câmera...")
                foto_base64 = request.POST.get('foto_camera')
                if not foto_base64:
                    return render(request, 'cadastrar_rosto.html', {
                        'interno': interno,
                        'mensagem': 'Nenhuma imagem foi capturada.'
                    })

                # Processar imagem base64
                formato, imagem_base64 = foto_base64.split(';base64,')
                if 'image/jpeg' not in formato.lower() and 'image/jpg' not in formato.lower():
                    return render(request, 'cadastrar_rosto.html', {
                        'interno': interno,
                        'mensagem': 'Formato de imagem não suportado. Use apenas JPG/JPEG.'
                    })

                imagem_decodificada = base64.b64decode(imagem_base64)
                img = Image.open(io.BytesIO(imagem_decodificada))

            else:  # Upload de arquivo
                print("Processando upload de arquivo...")
                if 'foto_upload' not in request.FILES:
                    return render(request, 'cadastrar_rosto.html', {
                        'interno': interno,
                        'mensagem': 'Nenhum arquivo foi enviado.'
                    })

                foto = request.FILES['foto_upload']
                if not foto.name.lower().endswith(('.jpg', '.jpeg')):
                    return render(request, 'cadastrar_rosto.html', {
                        'interno': interno,
                        'mensagem': 'Formato de arquivo não suportado. Use apenas JPG/JPEG.'
                    })

                img = Image.open(foto)

            # Converter para RGB (caso seja PNG ou outro formato)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Redimensionar imagem
            print(f"Dimensões originais: {img.width}x{img.height}")
            img.thumbnail((1000, 1000))  # Mantém aspect ratio
            print(f"Dimensões após redimensionamento: {img.width}x{img.height}")

            # Salvar no Cloudinary
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            nome_arquivo = f"foto_{interno.id}.jpg" if fonte_imagem == 'camera' else foto.name
            interno.foto.save(nome_arquivo, ContentFile(buffer.read()))
            print(f'foto salva')

            # Processar reconhecimento facial
            rgb_img = np.array(img)
            codificacoes = face_recognition.face_encodings(rgb_img)

            if len(codificacoes) > 0:
                interno.codificacao_facial = json.dumps(codificacoes[0].tolist())
                interno.save()
                return redirect('interno:detalhes_interno', interno_id=interno.id)
            else:
                # Remover a foto salva se nenhum rosto foi detectado
                interno.foto.delete(save=False)
                return render(request, 'cadastrar_rosto.html', {
                    'interno': interno,
                    'mensagem': 'Nenhum rosto detectado na imagem. Certifique-se que o rosto está visível e bem iluminado.'
                })

        except Exception as e:
            print(f"ERRO durante o processamento: {str(e)}")
            return render(request, 'cadastrar_rosto.html', {
                'interno': interno,
                'mensagem': f'Erro durante o processamento: {str(e)}'
            })

    return render(request, 'cadastrar_rosto.html', {'interno': interno})


def reconhecer_interno(request):
    print("\n=== NOVA REQUISIÇÃO RECEBIDA ===")
    print(f"Método: {request.method}")
    print(f"Content-Type: {request.content_type}")

    if request.method == 'POST':
        try:
            # Verifica se é FormData (upload de arquivo)
            if 'foto_upload' in request.FILES:
                print("[DEBUG] Modo upload de arquivo")
                foto = request.FILES['foto_upload']
                print(f"[DEBUG] Arquivo recebido: {foto.name} ({foto.size} bytes)")

                # Verificação de extensão antes de processar
                if not foto.name.lower().endswith(('.jpg', '.jpeg', '.jpe')):
                    print("[ERRO] Formato de arquivo não suportado")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Apenas arquivos JPG/JPEG são suportados'
                    }, status=400)

                # Processa diretamente da memória
                try:
                    image_stream = BytesIO(foto.read())
                    resultado = processar_imagem_da_memoria(image_stream)
                    print(f"[DEBUG] Resultado do processamento: {resultado}")
                    return JsonResponse(resultado)
                except Exception as e:
                    print(f"[ERRO] Falha no processamento do upload: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=500)

            # Verifica se é Blob (câmera)
            elif 'imagem' in request.FILES:
                print("[DEBUG] Modo câmera (Blob)")
                imagem_blob = request.FILES['imagem']
                print(f"[DEBUG] Tamanho do blob recebido: {imagem_blob.size} bytes")

                # Processa diretamente da memória
                try:
                    image_stream = BytesIO(imagem_blob.read())
                    resultado = processar_imagem_da_memoria(image_stream)
                    print(f"[DEBUG] Resultado do processamento: {resultado}")
                    return JsonResponse(resultado)
                except Exception as e:
                    print(f"[ERRO] Falha no processamento do blob: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=500)

            # Modo legado (base64 - mantido para compatibilidade)
            elif 'foto_camera' in request.POST:
                print("[DEBUG] Modo legado (base64)")
                foto_base64 = request.POST.get('foto_camera')
                if not foto_base64:
                    print("[ERRO] Nenhuma imagem capturada")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Nenhuma imagem capturada'
                    }, status=400)

                try:
                    # Processamento da imagem base64
                    if ';base64,' in foto_base64:
                        foto_base64 = foto_base64.split(';base64,')[1]

                    imagem_decodificada = base64.b64decode(foto_base64)
                    image_stream = BytesIO(imagem_decodificada)
                    resultado = processar_imagem_da_memoria(image_stream)
                    print(f"[DEBUG] Resultado do processamento: {resultado}")
                    return JsonResponse(resultado)

                except Exception as e:
                    print(f"[ERRO] Falha no processamento base64: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=500)

            else:
                print("[ERRO] Formato de requisição inválido")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Formato de requisição inválido'
                }, status=400)

        except Exception as e:
            print(f"[ERRO CRÍTICO] Falha no processamento: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Erro interno no servidor'
            }, status=500)

    print("[DEBUG] Requisição GET recebida - exibindo página")
    return render(request, 'reconhecer_interno.html')


def processar_imagem_da_memoria(image_stream):
    """
    Processa imagens JPG/JPEG para reconhecimento facial
    Versão simplificada que rejeita outros formatos
    """
    print("[DEBUG] Processando imagem (versão JPG/JPEG only)")
    try:
        # 1. Verificar se é JPG/JPEG
        header = image_stream.read(4)
        image_stream.seek(0)

        if not header.startswith(b'\xFF\xD8'):
            print("[ERRO] Formato não é JPG/JPEG")
            return {'status': 'error', 'message': 'Apenas imagens JPG/JPEG são suportadas'}

        # 2. Carregar imagem
        try:
            pil_image = Image.open(image_stream)
            print(f"[DEBUG] Imagem carregada. Formato: {pil_image.format}, Modo: {pil_image.mode}")

            # Verificação adicional de formato
            if pil_image.format not in ('JPEG', 'JPG'):
                print(f"[ERRO] Formato real: {pil_image.format} (esperado JPEG/JPG)")
                return {'status': 'error', 'message': 'Formato de arquivo inválido'}
        except Exception as e:
            print(f"[ERRO] Falha ao abrir imagem: {str(e)}")
            return {'status': 'error', 'message': 'Falha ao ler imagem'}

        # 3. Conversão garantida para RGB (embora JPG já deva ser RGB)
        if pil_image.mode != 'RGB':
            print(f"[DEBUG] Convertendo de {pil_image.mode} para RGB")
            pil_image = pil_image.convert('RGB')

        # 4. Conversão para array numpy
        try:
            image_array = np.array(pil_image)
            print(f"[DEBUG] Array numpy criado. Dimensões: {image_array.shape}")
        except Exception as e:
            print(f"[ERRO] Falha na conversão para array: {str(e)}")
            return {'status': 'error', 'message': 'Falha ao processar imagem'}

        # 5. Detecção facial
        try:
            codificacoes = face_recognition.face_encodings(image_array)

            if not codificacoes:
                print("[DEBUG] Nenhum rosto detectado")
                return {'status': 'no_face', 'message': 'Nenhum rosto detectado'}

            print(f"[DEBUG] {len(codificacoes)} rosto(s) detectado(s)")
            codificacao_desconhecida = codificacoes[0]
        except Exception as e:
            print(f"[ERRO] Falha na detecção facial: {str(e)}")
            return {'status': 'error', 'message': 'Falha no reconhecimento facial'}

        # 6. Busca no banco de dados
        print("[DEBUG] Buscando internos no banco de dados...")
        from .models import Interno
        internos = Interno.objects.exclude(codificacao_facial__isnull=True).only(
            'id', 'nome', 'prontuario', 'unidade', 'codificacao_facial'
        )
        print(f"[DEBUG] {len(internos)} internos com codificação facial")

        resultados = []
        for interno in internos:
            try:
                codificacao_cadastrada = json.loads(interno.codificacao_facial)
                distancia = face_recognition.face_distance([codificacao_cadastrada], codificacao_desconhecida)[0]

                if distancia < 0.6:  # Limite de similaridade
                    resultados.append({
                        'id': interno.id,
                        'nome': interno.nome,
                        'prontuario': interno.prontuario,
                        'unidade': str(interno.unidade),
                        'distancia': float(distancia),
                        'status': 'recognized'
                    })
            except Exception as e:
                print(f"[AVISO] Erro ao processar interno {interno.id}: {str(e)}")
                continue


        if resultados:
            resultados.sort(key=lambda x: x['distancia'])
            for resultado in resultados:
                interno = Interno.objects.get(id=resultado['id'])
                resultado.update({
                    'foto_url': interno.foto.url if interno.foto else '/static/images/default-profile.png',
                    'detalhes_url': reverse('interno:detalhes_interno', kwargs={'interno_id': interno.id})
                })
            print(f"[DEBUG] Melhor match: {resultados[0]['nome']} (Distância: {resultados[0]['distancia']})")
            return {'status': 'success', 'resultados': resultados}

        print("[DEBUG] Nenhum interno reconhecido")
        return {'status': 'unknown', 'message': 'Nenhum interno reconhecido'}

    except Exception as e:
        print(f"[ERRO CRÍTICO] {str(e)}")
        return {'status': 'error', 'message': 'Erro interno no processamento'}


def processar_reconhecimento_rapido(request):
    print("\n[DEBUG] Iniciando processamento rápido (AJAX)")
    try:
        foto_base64 = request.POST.get('imagem')
        if not foto_base64:
            print("[ERRO] Nenhuma imagem recebida na requisição AJAX")
            return JsonResponse({'error': 'Nenhuma imagem recebida'}, status=400)

        print("[DEBUG] Decodificando imagem base64...")
        # Extrai apenas a parte dos dados da string base64
        if ';base64,' in foto_base64:
            foto_base64 = foto_base64.split(';base64,')[1]

        imagem_decodificada = base64.b64decode(foto_base64)

        # Processa diretamente da memória sem salvar em arquivo
        print("[DEBUG] Processando imagem da memória...")
        try:
            # Cria um objeto de arquivo em memória
            from io import BytesIO
            image_stream = BytesIO(imagem_decodificada)

            # Processa diretamente do stream
            resultado = processar_imagem_da_memoria(image_stream)
            print(f"[DEBUG] Resultado do processamento rápido: {resultado}")

            return JsonResponse(resultado)

        except Exception as e:
            print(f"[ERRO] Falha no processamento direto: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        print(f"[ERRO] Falha no processamento rápido: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)




BATCH_SIZE = 1000  # Define o tamanho dos lotes


def save_in_batches(model, instances, fields=None):
    """Salva registros em lotes para evitar erro de muitas variáveis SQL."""
    print(f"📊 Salvando {len(instances)} registros em lotes de {BATCH_SIZE}.")
    for i in range(0, len(instances), BATCH_SIZE):
        batch = instances[i:i + BATCH_SIZE]
        print(f"🔄 Processando lote {i // BATCH_SIZE + 1}: {len(batch)} registros.")
        try:
            if fields:
                model.objects.bulk_update(batch, fields)  # Atualização em lote
            else:
                model.objects.bulk_create(batch, ignore_conflicts=True)  # ⚠️ Evita erro de unicidade
        except Exception as e:
            print(f"❌ Erro ao processar o lote {i // BATCH_SIZE + 1}: {e}")
            raise


def upload_planilha_excel(request):
    print("📢 Iniciando upload da planilha...")


    if request.method == 'POST':
        print("📥 Método POST detectado.")
        form = UploadExcelInternosForm(request.POST, request.FILES)

        if form.is_valid():
            print("✅ Formulário válido.")
            arquivo = request.FILES['arquivo']

            try:
                df = pd.read_excel(arquivo)
                print(f"📊 Planilha carregada com {len(df)} registros.")

                # Criar um log para registrar alterações

                csv_log = "log_atualizacoes.csv"

                log_entries = []  # Lista para armazenar logs
                novo_interno = []  # lista internos novos adicionados
                atualizacoes = []

                # Iterar pelos registros do Excel
                for index, row in df.iterrows():

                    # Converte os valores para string e remove espaços em branco
                    prontuario = str(row.get('prontuario', '')).strip()
                    nome = str(row.get('nome', '')).strip()
                    cpf = str(row.get('cpf', '')).strip()
                    nome_mae = str(row.get('nome_mae', '')).strip()

                    # Tratando a unidade para garantir que valores 'NaN' sejam tratados corretamente
                    unidade = row.get('unidade', '')  # Atribui valor vazio se não encontrar o campo
                    if pd.isna(unidade) or unidade == 'nan':  # Verifica se é NaN ou 'nan'
                        unidade = ''  # Substitui por string vazia

                    else:
                        unidade = str(unidade).strip()  # Converte para string e remove espaços, caso contrário
                    status = str(row.get('status', '')).strip()

                    # Garantir que data_extracao seja uma data normal (date)
                    data_extracao = row.get('data_extracao')
                    if not data_extracao or pd.isna(data_extracao):
                        data_extracao = timezone.now()
                    else:
                        try:
                            # Converte de "DD-MM-YYYY" para "YYYY-MM-DD"
                            data_extracao = datetime.strptime(data_extracao, "%d-%m-%Y").date()
                        except ValueError:
                            raise ValueError(f"Data inválida: {data_extracao}")

                    # Buscar o interno no banco

                    interno = Interno.objects.filter(prontuario=prontuario).first()

                    if interno:

                        # Comparar campos para ver se há mudanças
                        alterado = False
                        campos_modificados = []

                        if interno.nome != nome:
                            interno.nome = nome
                            campos_modificados.append("nome")
                            alterado = True

                        if interno.cpf != cpf:
                            interno.cpf = cpf
                            campos_modificados.append("cpf")
                            alterado = True

                        if interno.nome_mae != nome_mae:
                            interno.nome_mae = nome_mae
                            campos_modificados.append("nome_mae")
                            alterado = True

                        if interno.unidade != unidade:
                            interno.unidade = unidade
                            campos_modificados.append("unidade")
                            alterado = True

                        if interno.status != status:
                            interno.status = status
                            campos_modificados.append("status")
                            alterado = True

                        # Só atualiza a `data_extracao` se algum outro campo mudou
                        if alterado:
                            interno.data_extracao = data_extracao
                            campos_modificados.append("data_extracao")

                            # Salvar no banco de dados
                            print(f"💾 Salvando interno atualizado: {interno}")
                            interno.save()

                            # Criar log
                            log_entries.append(
                                [prontuario, ", ".join(campos_modificados), str(timezone.now())])
                            atualizacoes.append(prontuario)

                    else:
                        print(f"❌ Interno não encontrado. Criando novo registro.")
                        # Criar um novo registro
                        novo_interno = Interno(
                            prontuario=prontuario,
                            nome=row["nome"],
                            cpf=row["cpf"],
                            nome_mae=row["nome_mae"],
                            unidade=row["unidade"],
                            status=row["status"],
                            data_extracao=data_extracao,
                        )
                        print(f"💾 Salvando novo interno: {novo_interno}")
                        novo_interno.save()
                        novo_interno.append(prontuario)

                        # Criar log de novo registro
                        log_entries.append([prontuario, "Novo Registro", str(timezone.now())])



                # Salvar log em CSV
                print(f"📝 Salvando log em CSV no arquivo {csv_log}")
                log_df = pd.DataFrame(log_entries, columns=["Prontuario", "Campos Modificados", "Data"])
                log_df.to_csv(csv_log, mode="a", header=not os.path.exists(csv_log), index=False)


                print("✅ Atualização concluída!")

                messages.success(request,
                                 f"Planilha processada! {len(novo_interno)} adicionados, {len(atualizacoes)} atualizados.")
                return redirect('interno:upload_interno')

            except Exception as e:
                print(f"❌ Erro ao processar a planilha: {e}")
                messages.error(request, f"Erro ao processar a planilha: {e}")

    else:
        messages.error(request, f"Erro ao processar a planilha:")
        form = UploadExcelInternosForm()

    return render(request, 'upload_interno.html', {'form': form})


class Internos(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "interno.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe', 'DiretorUnidade']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        queryset = Interno.objects.all()

        return queryset.order_by('-prontuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        internos_cadastrados = Interno.objects.count()
        context['internos_cadastrados'] = internos_cadastrados

        return context


class RelatorioInterno(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "relatorio_interno.html"
    context_object_name = 'internos'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe', 'DiretorUnidade']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        query = self.request.GET.get('query', '')

        queryset = Interno.objects.all()

        # Filtro geral por nome, se o campo 'query' for usado
        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query)
            )

        # Filtro por status
        stat = self.request.GET.get('stat')
        if stat:
            queryset = queryset.filter(status=stat)

        # Filtro por unidade
        unidade = self.request.GET.get('unidade')
        if unidade:
            if unidade == "Sem unidade":
                queryset = queryset.filter(unidade__isnull=True)
            else:
                queryset = queryset.filter(unidade=unidade)

        # Filtro por CPF
        cpf = self.request.GET.get('cpf')
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)

        # Filtro por nome da mãe
        nome_mae = self.request.GET.get('nome_mae')
        if nome_mae:
            queryset = queryset.filter(nome_mae__icontains=nome_mae)

        # Filtro por prontuário
        prontuario = self.request.GET.get('prontuario')
        if prontuario:
            queryset = queryset.filter(prontuario__icontains=prontuario)

        return queryset.order_by('-prontuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Paginação personalizada
        page_obj = context['page_obj']
        paginator = page_obj.paginator
        page_range = paginator.page_range

        # Lógica para limitar a exibição das páginas
        if page_obj.number > 3:
            start = page_obj.number - 2
        else:
            start = 1

        if page_obj.number < paginator.num_pages - 2:
            end = page_obj.number + 2
        else:
            end = paginator.num_pages

        context['page_range'] = range(start, end + 1)

        interno = Interno.objects.all()
        context['interno'] = interno


        # manter campos preenchidos
        context['query'] = self.request.GET.get('query', '')
        context['nome_mae'] = self.request.GET.get('nome_mae', '')
        context['cpf'] = self.request.GET.get('cpf', '')
        context['prontuario'] = self.request.GET.get('prontuario', '')




        # # Ajuste aqui: mudando 'unidade' para 'unidades'
        unidades = Interno.objects.values_list('unidade', flat=True).distinct().order_by('unidade')
        # Substituindo 'None' por "Sem unidade"
        unidades = ['Sem unidade' if unidade is None else unidade for unidade in unidades]

        context['unidades'] = unidades

        context['status'] = Interno.objects.values_list('status', flat=True).distinct()

        return context

#populacao edit

class PopulacaoEdit(LoginRequiredMixin, UpdateView, UserPassesTestMixin):
    model = PopulacaoCarceraria
    form_class = PopulacaoCarcerariaForm
    template_name = 'populacao/populacao_edit.html'
    success_url = reverse_lazy('interno:interno')  # Redirecionar para a página de sucesso

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerGesipe', 'EditInterno', 'DiretorUnidade']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)


    # def get_form_kwargs(self):
    #     """Passa o formato correto da data para o formulário."""
    #     kwargs = super().get_form_kwargs()
    #     if self.object:
    #         # Ajusta o valor da data para o formato 'yyyy-mm-dd'
    #         kwargs['initial'] = {
    #             'data': self.object.data.strftime('%Y-%m-%d'),
    #         }
    #     return kwargs

    def form_valid(self, form):
        if self.request.POST.get('action') == 'delete':
            # Lida com a exclusão do registro
            self.object.delete()
            messages.error(self.request, 'Atualização excluída com sucesso!')
            return redirect(self.success_url)

        # Atualiza os dados do registro
        populacao = form.save(commit=False)
        populacao.save()

        messages.success(self.request, 'População atualizada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
