from django.shortcuts import render, redirect
from interno.models import Interno
from .forms import OcorrenciaPlantaoForm
from .models import OcorrenciaPlantao
from interno.models import PopulacaoCarceraria
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, FormView, View, UpdateView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import JsonResponse
from servidor.models import Servidor
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, OuterRef, Subquery, Sum
import json
from seappb.models import Unidade
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date

# Create your views here.

# buscar populacao atualizada


class PopulacaoCarcerariaAPIView(View):
    def get(self, request):
        unidade_id = request.GET.get('unidade_id')

        if not unidade_id:
            return JsonResponse({'error': 'unidade_id parameter is required'}, status=400)

        try:
            # Busca o registro mais recente para a unidade
            populacao = PopulacaoCarceraria.objects.filter(unidade_id=unidade_id).latest('data_atualizacao')
            print(f'{populacao}')

            data = {
                'regime_aberto': populacao.regime_aberto,
                'regime_semiaberto': populacao.regime_semiaberto,
                'regime_fechado': populacao.regime_fechado,
                'regime_domiciliar': populacao.regime_domiciliar,
                'provisorio': populacao.provisorio,
                'sentenciado': populacao.sentenciado,
                'masculino': populacao.masculino,
                'feminino': populacao.feminino,
                'total': populacao.total,
            }

            return JsonResponse(data)

        except ObjectDoesNotExist:
            return JsonResponse({})  # Retorna objeto vazio se não encontrar dados
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def buscar_servidor_list(request):
    matricula = request.GET.get('matricula', '').strip()

    if not matricula:
        return JsonResponse({'error': 'Matrícula não fornecida'}, status=400)

    try:
        servidor = Servidor.objects.get(matricula=matricula)
        return JsonResponse({
            'id': servidor.id,
            'matricula': servidor.matricula,
            'nome': servidor.nome,
            'cargo': servidor.cargo
        })
    except Servidor.DoesNotExist:
        return JsonResponse({'error': 'Servidor não encontrado'}, status=404)


class GestaoPrisional(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "gestao_prisional.html"
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



        # Subquery: pega o registro mais recente por unidade
        subquery = PopulacaoCarceraria.objects.filter(
            unidade=OuterRef('unidade')
        ).order_by('-data_atualizacao')

        latest_records = PopulacaoCarceraria.objects.filter(
            pk=Subquery(subquery.values('pk')[:1])  # só o mais recente por unidade
        )

        # Total geral da população carcerária
        total_populacao = sum(record.total for record in latest_records)
        print("Total geral da população carcerária:", total_populacao)

        # Dados para o gráfico de barra: população por unidade
        bar_labels = [record.unidade.nome for record in latest_records]
        bar_values = [record.total for record in latest_records]

        print("População por unidade:")
        for nome, total in zip(bar_labels, bar_values):
            print(f"{nome}: {total}")

        # Dados para o gráfico de barra: população por reisp
        populacao_por_reisp = (
            latest_records
            .values('unidade__reisp')
            .annotate(total=Sum('total'))
            .order_by('unidade__reisp')
        )

        # Labels dos REISPs (transformar número em string tipo "1º REISP")
        reisp_labels = [f"{item['unidade__reisp']}º REISP" if item['unidade__reisp'] else 'Não informado' for item in
                        populacao_por_reisp]
        reisp_values = [item['total'] for item in populacao_por_reisp]

        # Ordena os registros por total diretamente na hora de gerar os dados
        sorted_records = sorted(latest_records, key=lambda r: r.total, reverse=True)

        # Salvando no contexto
        context['total_populacao'] = total_populacao
        context['bar_labels'] = json.dumps([r.unidade.nome for r in sorted_records])
        context['bar_values'] = json.dumps([r.total for r in sorted_records])
        context['bar_labels_reisp'] = reisp_labels
        context['bar_values_reisp'] = reisp_values



        #internos cadastrados
        internos_cadastrados = Interno.objects.count()
        context['internos_cadastrados'] = internos_cadastrados

        # Data mais recente geral
        latest_date = PopulacaoCarceraria.objects.aggregate(Max('data_atualizacao'))['data_atualizacao__max']

        ticker_data = []

        if latest_date:
            current_month_start = latest_date.replace(day=1)
            previous_month_end = current_month_start - timedelta(days=1)
            previous_month_start = previous_month_end.replace(day=1)

            unidades = Unidade.objects.all()

            for unidade in unidades:
                # Último registro no mês atual
                atual = PopulacaoCarceraria.objects.filter(
                    unidade=unidade,
                    data_atualizacao__year=current_month_start.year,
                    data_atualizacao__month=current_month_start.month
                ).order_by('-data_atualizacao').first()

                # Último registro no mês anterior
                anterior = PopulacaoCarceraria.objects.filter(
                    unidade=unidade,
                    data_atualizacao__year=previous_month_start.year,
                    data_atualizacao__month=previous_month_start.month
                ).order_by('-data_atualizacao').first()

                if atual:
                    variacao = 0
                    if anterior and anterior.total != 0:
                        try:
                            variacao = ((atual.total - anterior.total) / anterior.total) * 100
                        except ZeroDivisionError:
                            variacao = 0

                    ticker_data.append({
                        'unidade': unidade.nome,
                        'populacao': atual.total,
                        'variacao': round(variacao, 1)
                    })

                # Ordenar o ticker_data pela população em ordem decrescente
            ticker_data = sorted(ticker_data, key=lambda x: x['populacao'], reverse=True)

        context['ticker_data'] = ticker_data
        print(ticker_data)


        # grafico com historico mensal

        # Dicionário com os nomes dos meses em português
        meses_em_portugues = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro"
        }

        # Data atual e data de 12 meses atrás
        hoje = now().date()
        doze_meses_atras = hoje - relativedelta(months=12)

        # Consulta agrupando por mês
        populacao_mensal = (
            PopulacaoCarceraria.objects.filter(data_atualizacao__gte=doze_meses_atras)
            .annotate(mes=TruncMonth('data_atualizacao'))
            .values('mes')
            .annotate(total=Sum('total'))
            .order_by('mes')
        )

        # Converter os labels para "MÊS/ANO" (ex: Março/2025)
        bar_labels_mensal = [
            f"{meses_em_portugues[item['mes'].month]}/{item['mes'].year}"
            for item in populacao_mensal
        ]
        bar_values_mensal = [item['total'] for item in populacao_mensal]

        context['bar_labels_mensal'] = json.dumps(bar_labels_mensal)
        context['bar_values_mensal'] = json.dumps(bar_values_mensal)


        return context


# ocorrencia plantoes


class OcorrenciaPlantaoAddView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = OcorrenciaPlantaoForm
    template_name = 'ocorrencia_plantao/ocorrencia_plantao_add.html'
    success_url = reverse_lazy('gestao_prisional:gestao_prisional')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        try:
            user = self.request.user

            # Valida os servidores ordinários
            ordinario_ids = [int(id) for id in self.request.POST.get('ordinario_ids', '').split(',') if id]
            if not ordinario_ids:
                messages.error(self.request, "Adicione pelo menos um servidor ordinário.")
                return self.form_invalid(form)

            # Salva os dados usando o método save() do form
            plantao = form.save(user)

            messages.success(self.request, "Plantão registrado com sucesso!")
            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f"Erro ao registrar plantão: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{form.fields[field].label if field in form.fields else 'Erro'}: {error}"
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:

            subquery = PopulacaoCarceraria.objects.values('unidade').annotate(
                latest_date=Max('data_atualizacao')
            )

            latest_records = PopulacaoCarceraria.objects.filter(
                data_atualizacao__in=subquery.values('latest_date'),
                unidade__in=subquery.values('unidade')
            )

            context['total_populacao'] = sum(record.total for record in latest_records)

        except Exception as e:
            print(f"Erro ao calcular total geral: {e}")
            context['total_populacao'] = 0

        return context


class RelatorioOcorrenciaPlantao(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = OcorrenciaPlantao
    template_name = "ocorrencia_plantao/relatorio_ocorrencia_plantao.html"
    context_object_name = 'ocorrencias'
    paginate_by = 50

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        data_inicial = self.request.GET.get('dataInicial')
        data_final = self.request.GET.get('dataFinal')
        unidade_id = self.request.GET.get('unidade')
        query = self.request.GET.get('query', '')

        # Datas padrão (mês atual)
        today = now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        data_inicial = parse_date(data_inicial) if data_inicial else first_day_of_month
        data_final = parse_date(data_final) if data_final else last_day_of_month

        queryset = OcorrenciaPlantao.objects.select_related(
            'chefe_equipe', 'unidade', 'usuario'
        ).prefetch_related(
            'servidores_ordinario', 'servidores_extraordinario'
        )

        # Filtros
        if unidade_id:
            queryset = queryset.filter(unidade_id=unidade_id)

        if query:
            queryset = queryset.filter(
                Q(chefe_equipe__nome__icontains=query) |
                Q(descricao__icontains=query) |
                Q(observacao__icontains=query)
            )

        # Filtro por data
        queryset = queryset.filter(data__range=[data_inicial, data_final])

        return queryset.order_by('-data')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datas para o template
        today = now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        data_inicial = self.request.GET.get('dataInicial', first_day_of_month)
        data_final = self.request.GET.get('dataFinal', last_day_of_month)

        context.update({
            'query': self.request.GET.get('query', ''),
            'dataInicial': data_inicial.strftime('%Y-%m-%d') if hasattr(data_inicial, 'strftime') else data_inicial,
            'dataFinal': data_final.strftime('%Y-%m-%d') if hasattr(data_final, 'strftime') else data_final,
            'unidades': Unidade.objects.all().order_by('nome'),
            'user_groups': self.request.user.groups.values_list('name', flat=True),
        })

        return context


class DetalhesOcorrenciaPlantao(LoginRequiredMixin, DetailView):
    model = OcorrenciaPlantao
    template_name = "ocorrencia_plantao/detalhes_ocorrencia.html"
    context_object_name = 'ocorrencia'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ocorrencia = self.get_object()

        # Obter população carcerária associada
        try:
            context['populacao'] = PopulacaoCarceraria.objects.get(plantao=ocorrencia)
        except PopulacaoCarceraria.DoesNotExist:
            context['populacao'] = None

        # Verificar se usuário pode editar
        context['pode_editar'] = self.request.user == ocorrencia.usuario or self.request.user.is_superuser

        return context


class EditarOcorrenciaPlantao(LoginRequiredMixin, UpdateView):
    model = OcorrenciaPlantao
    form_class = OcorrenciaPlantaoForm
    template_name = "ocorrencia_plantao/editar_ocorrencia.html"

    def get_success_url(self):
        return reverse_lazy('gestao_prisional:ocorrencia-detalhes', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        ocorrencia = self.get_object()

        # Preencher dados iniciais do formulário
        try:
            populacao = PopulacaoCarceraria.objects.get(plantao=ocorrencia)
            initial.update({
                'regime_aberto': populacao.regime_aberto,
                'regime_semiaberto': populacao.regime_semiaberto,
                'regime_fechado': populacao.regime_fechado,
                'regime_domiciliar': populacao.regime_domiciliar,
                'provisorio': populacao.provisorio,
                'sentenciado': populacao.sentenciado,
                'masculino': populacao.masculino,
                'feminino': populacao.feminino,
            })
        except PopulacaoCarceraria.DoesNotExist:
            pass

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ocorrencia = self.get_object()

        # Adicionar servidores para o template
        context['servidores_ordinario'] = ocorrencia.servidores_ordinario.all()
        context['servidores_extraordinario'] = ocorrencia.servidores_extraordinario.all()

        return context

    def form_valid(self, form):
        # Verificar permissão antes de salvar
        if self.request.user != self.object.usuario and not self.request.user.is_superuser:
            messages.error(self.request, "Você não tem permissão para editar esta ocorrência.")
            return self.form_invalid(form)

        # Processar dados do formulário
        response = super().form_valid(form)

        # Atualizar população carcerária
        populacao, created = PopulacaoCarceraria.objects.get_or_create(
            plantao=self.object,
            defaults={
                'data_atualizacao': form.cleaned_data['data'],
                'unidade': form.cleaned_data['unidade'],
                'usuario': self.request.user
            }
        )

        # Atualizar campos
        for field in ['regime_aberto', 'regime_semiaberto', 'regime_fechado',
                      'regime_domiciliar', 'provisorio', 'sentenciado',
                      'masculino', 'feminino']:
            setattr(populacao, field, form.cleaned_data[field])

        populacao.save()

        messages.success(self.request, "Ocorrência atualizada com sucesso!")
        return response
