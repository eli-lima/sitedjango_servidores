
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
from django.urls import reverse_lazy

#modulo facial


def detalhes_interno(request, interno_id):
    interno = get_object_or_404(Interno, id=interno_id)
    return render(request, 'detalhes_interno.html', {'interno': interno})


@csrf_exempt
def cadastrar_rosto(request, interno_id):
    interno = get_object_or_404(Interno, id=interno_id)

    if request.method == 'POST':
        fonte_imagem = request.POST.get('fonte_imagem')  # Verifica a fonte da imagem (câmera ou upload)

        if fonte_imagem == 'camera':
            # Processa a imagem capturada pela câmera (base64)
            foto_base64 = request.POST.get('foto_camera')
            if foto_base64:
                formato, imagem_base64 = foto_base64.split(';base64,')
                extensao = formato.split('/')[-1]  # Obtém a extensão da imagem (ex: jpeg)
                imagem_decodificada = base64.b64decode(imagem_base64)
                file_name = f"temp_foto.{extensao}"
                file_path = default_storage.save(file_name, ContentFile(imagem_decodificada))
            else:
                return render(request, 'cadastrar_rosto.html',
                              {'interno': interno, 'mensagem': 'Nenhuma imagem foi capturada.'})
        else:
            # Processa o arquivo enviado pelo upload
            if 'foto_upload' in request.FILES:
                foto = request.FILES['foto_upload']
                file_name = default_storage.save(foto.name, foto)
                file_path = default_storage.path(file_name)
            else:
                return render(request, 'cadastrar_rosto.html',
                              {'interno': interno, 'mensagem': 'Nenhum arquivo foi enviado.'})

        # Carrega a imagem e gera a codificação facial
        imagem = face_recognition.load_image_file(default_storage.path(file_path))
        codificacoes = face_recognition.face_encodings(imagem)

        if len(codificacoes) > 0:
            codificacao = codificacoes[0]
            interno.codificacao_facial = json.dumps(codificacao.tolist())  # Salva a codificação como JSON
            if fonte_imagem == 'camera':
                interno.foto.save(f"foto_{interno.id}.{extensao}",
                                  ContentFile(imagem_decodificada))  # Salva a foto da câmera
            else:
                interno.foto.save(foto.name, foto)  # Salva a foto do upload
            interno.save()
            default_storage.delete(file_path)  # Remove a imagem temporária
            return redirect('interno:detalhes_interno', interno_id=interno.id)
        else:
            default_storage.delete(file_path)
            return render(request, 'cadastrar_rosto.html',
                          {'interno': interno, 'mensagem': 'Nenhum rosto detectado na imagem.'})

    return render(request, 'cadastrar_rosto.html', {'interno': interno})


def reconhecer_interno(request):
    if request.method == 'POST':
        fonte_imagem = request.POST.get('fonte_imagem')  # Verifica a fonte da imagem (câmera ou upload)

        if fonte_imagem == 'camera':
            # Processa a imagem capturada pela câmera (base64)
            foto_base64 = request.POST.get('foto_camera')
            if foto_base64:
                formato, imagem_base64 = foto_base64.split(';base64,')
                extensao = formato.split('/')[-1]  # Obtém a extensão da imagem (ex: jpeg)
                imagem_decodificada = base64.b64decode(imagem_base64)
                file_name = f"temp_foto.{extensao}"
                file_path = default_storage.save(file_name, ContentFile(imagem_decodificada))
            else:
                return render(request, 'reconhecer_interno.html', {'mensagem': 'Nenhuma imagem foi capturada.'})
        else:
            # Processa o arquivo enviado pelo upload
            if 'foto_upload' in request.FILES:
                foto = request.FILES['foto_upload']
                file_name = default_storage.save(foto.name, foto)
                file_path = default_storage.path(file_name)
            else:
                return render(request, 'reconhecer_interno.html', {'mensagem': 'Nenhum arquivo foi enviado.'})

        # Carrega a imagem e gera a codificação facial
        imagem = face_recognition.load_image_file(default_storage.path(file_path))
        codificacoes = face_recognition.face_encodings(imagem)

        if len(codificacoes) > 0:
            codificacao_desconhecida = codificacoes[0]

            # Compara com as codificações dos internos cadastrados
            for interno in Interno.objects.exclude(codificacao_facial__isnull=True):
                codificacao_cadastrada = json.loads(interno.codificacao_facial)
                resultado = face_recognition.compare_faces([codificacao_cadastrada], codificacao_desconhecida)

                if resultado[0]:
                    default_storage.delete(file_path)  # Remove a imagem temporária
                    return render(request, 'resultado.html', {'interno': interno})

            default_storage.delete(file_path)
            return render(request, 'resultado.html', {'mensagem': 'Nenhum interno reconhecido.'})
        else:
            default_storage.delete(file_path)
            return render(request, 'resultado.html', {'mensagem': 'Nenhum rosto detectado na imagem.'})

    return render(request, 'reconhecer_interno.html')



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
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
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
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
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
        grupos_permitidos = ['Administrador', 'GerGesipe', 'EditInterno']
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
