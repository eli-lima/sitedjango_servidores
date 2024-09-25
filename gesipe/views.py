from django.shortcuts import render, redirect
from .models import Gesipe_adm
from django.views.generic.edit import FormView, UpdateView, CreateView, View
from django.utils.timezone import now
from .forms import GesipeAdmForm, UploadFileForm
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q  # Para pesquisas com OR lógico
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from datetime import datetime, date
import openpyxl


# Create your views here.

# url - view - html


class Gesipe(LoginRequiredMixin, ListView):
    template_name = "gesipe.html"
    model = Gesipe_adm
    paginate_by = 10
    ordering = ['data']

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        queryset = super().get_queryset()

        if query:
            # Tentar interpretar 'query' como data nos formatos DD/MM/YYYY, DD-MM-YYYY ou YYYY-MM-DD
            data_pesquisa = self.parse_data(query)
            if data_pesquisa:
                queryset = queryset.filter(data=data_pesquisa)
            else:
                # Pesquisa normal por outros campos se não for data
                queryset = queryset.filter(
                    Q(usuario__username__icontains=query) |
                    Q(total__icontains=query)
                )

        return queryset

    def post(self, request, *args, **kwargs):
        data_pesquisa = request.POST.get('data_pesquisa')

        if data_pesquisa:
            # Tentar interpretar a data nos formatos permitidos
            data_pesquisa = self.parse_data(data_pesquisa)
            if not data_pesquisa:
                return JsonResponse({'error': 'Data inválida'}, status=400)

            if Gesipe_adm.objects.filter(data=data_pesquisa).exists():
                existing_record = Gesipe_adm.objects.get(data=data_pesquisa)
                edit_url = reverse('gesipe:gesipe_adm_edit', kwargs={'pk': existing_record.pk})
                return JsonResponse({'exists': True, 'url': edit_url})
            else:
                create_url = reverse('gesipe:gesipe_adm')
                return JsonResponse({'exists': False, 'url': create_url})

        return JsonResponse({'error': 'Data não fornecida'}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')

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

        return context

    def parse_data(self, date_str):
        """
        Tenta fazer o parsing de uma string de data nos formatos DD/MM/YYYY, DD-MM-YYYY e YYYY-MM-DD.
        Retorna a data no formato 'datetime.date' se válido, senão retorna None.
        """
        date_formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None


class GesipeAdm(LoginRequiredMixin, CreateView):
    model = Gesipe_adm
    form_class = GesipeAdmForm
    template_name = 'gesipe_adm.html'
    success_url = reverse_lazy('gesipe:gesipe_adm')

    def form_valid(self, form):
        # Se o formulário passar pela validação, salva o novo registro
        print("Formulário válido, salvando dados...")
        dados_adm = form.save(commit=False)
        dados_adm.usuario = self.request.user  # Atribui o usuário atual
        dados_adm.data_edicao = timezone.now()  # Define a data de edição
        dados_adm.save()
        messages.success(self.request, 'Dados adicionados com sucesso!')
        return redirect(self.success_url)

    def form_invalid(self, form):

        if 'data' in form.errors:
            # Exibe uma mensagem de erro personalizada

            messages.error(self.request, 'Registro para a data já existe. Utilize a opção de edição para alterar os dados.')
        else:
            pass

        # Retorna o formulário inválido para o template com a mensagem de erro
        return self.render_to_response(self.get_context_data(form=form))


class GesipeAdmEdit(LoginRequiredMixin, UpdateView):
    model = Gesipe_adm
    form_class = GesipeAdmForm
    template_name = 'gesipe_adm_edit.html'
    success_url = reverse_lazy('gesipe:gesipe_adm')  # Redirecionar para a página de sucesso

    def get_form_kwargs(self):
        """Passa o formato correto da data para o formulário."""
        kwargs = super().get_form_kwargs()
        if self.object:
            # Ajusta o valor da data para o formato 'yyyy-mm-dd'
            kwargs['initial'] = {
                'data': self.object.data.strftime('%Y-%m-%d'),
            }
        return kwargs

    def form_valid(self, form):
        if self.request.POST.get('action') == 'delete':
            # Lida com a exclusão do registro
            self.object.delete()
            messages.error(self.request, 'Registro excluído com sucesso!')
            return redirect(self.success_url)

        # Atualiza os dados do registro
        dados_adm = form.save(commit=False)
        dados_adm.data_edicao = timezone.now()  # Atualiza a data de edição
        dados_adm.save()

        messages.success(self.request, 'Dados atualizados com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formatted_date'] = self.object.data.strftime('%d/%m/%Y')
        return context



class GesipeAdmLote(LoginRequiredMixin, View):
    form_class = UploadFileForm
    template_name = 'gesipe_adm_lote.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            arquivo_excel = request.FILES['arquivo_excel']

            # Carregar a planilha com valores calculados em vez de fórmulas
            wb = openpyxl.load_workbook(arquivo_excel, data_only=True)
            sheet = wb['Planilha']  # Nome correto da aba

            try:
                for row in sheet.iter_rows(min_row=4, values_only=True):
                    if not any(row):  # Ignorar linhas em branco
                        continue

                    # Extrair o valor da data
                    data = row[0]  # Supondo que a data está na primeira coluna
                    print(data)

                    # Converter a data para o formato 'YYYY-MM-DD' se necessário
                    if isinstance(data, str):  # Se a data estiver como string
                        try:
                            data = datetime.strptime(data, '%d/%m/%Y').date()  # Converter de DD/MM/YYYY para objeto date
                        except ValueError:
                            messages.error(request, f'O formato de data "{data}" é inválido. Use o formato DD/MM/YYYY.')
                            return render(request, self.template_name, {'form': form})

                        # Continuar extraindo outros valores conforme o modelo
                        # processos = row[1] or 0
                        # memorandos_diarias = row[2] or 0
                        # memorandos_documentos_capturados = row[3] or 0
                        # despachos_gerencias = row[4] or 0
                        # despachos_unidades = row[5] or 0
                        # despachos_grupos = row[6] or 0
                        # oficios_internos_unidades_prisionais = row[7] or 0
                        # oficios_internos_setores_seap_pb = row[8] or 0
                        # oficios_internos_circular = row[9] or 0
                        # oficios_externos_seap_pb = row[10] or 0
                        # oficios_externos_diversos = row[11] or 0
                        # oficios_externos_judiciario = row[12] or 0
                        # os_grupos = row[13] or 0
                        # os_diversos = row[14] or 0
                        # portarias = row[15] or 0

                    # Verificar se um registro com essa data já existe

                    # Se 'created' for True, significa que o registro foi criado; se False, ele foi atualizado.
                    obj, created = Gesipe_adm.objects.update_or_create(
                        data=data,  # Critério de identificação pelo campo `data`
                        defaults={
                            'processos': 0 if row[1] is None else row[1],
                            'memorandos_diarias': 0 if row[2] is None else row[2],
                            'memorandos_documentos_capturados': 0 if row[3] is None else row[3],
                            'despachos_gerencias': 0 if row[4] is None else row[4],
                            'despachos_unidades': 0 if row[5] is None else row[5],
                            'despachos_grupos': 0 if row[6] is None else row[6],
                            'oficios_internos_unidades_prisionais': 0 if row[7] is None else row[7],
                            'oficios_internos_setores_seap_pb': 0 if row[8] is None else row[8],
                            'oficios_internos_circular': 0 if row[9] is None else row[9],
                            'oficios_externos_seap_pb': 0 if row[10] is None else row[10],
                            'oficios_externos_diversos': 0 if row[11] is None else row[11],
                            'oficios_externos_judiciario': 0 if row[12] is None else row[12],
                            'os_grupos': 0 if row[13] is None else row[13],
                            'os_diversos': 0 if row[14] is None else row[14],
                            'portarias': 0 if row[15] is None else row[15],
                            'usuario': request.user  # Assumindo que você quer armazenar o usuário que fez a alteração
                        }
                    )


                messages.success(request, 'Dados importados com sucesso!')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao processar o arquivo: {e}')

            return redirect('gesipe:gesipe_adm_lote')

        return render(request, self.template_name, {'form': form})