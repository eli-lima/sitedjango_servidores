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
from datetime import timedelta, date
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
    paginate_by = 50

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

        # 1. Obter parâmetros de filtro
        unidade_id = self.request.GET.get('unidade')
        mes = self.request.GET.get('mes')
        ano = self.request.GET.get('ano')

        # 2. Configurar filtros básicos
        filtros = {}
        filtros_servidor = {}

        if unidade_id and unidade_id != 'todas':
            unidade_filtrada = Unidade.objects.get(id=unidade_id)
            context.update({
                'filtro_unidade_especifica': True,
                'unidade_filtrada': unidade_filtrada
            })
            filtros['unidade_id'] = unidade_id
            filtros_servidor['local_trabalho'] = unidade_id
        else:
            context['filtro_unidade_especifica'] = False

        # 3. Configurar filtros de data
        context['tem_filtro_mes_ano'] = bool(mes and ano)
        data_inicio, data_fim = None, None

        if mes and ano:
            try:
                mes = int(mes)
                ano = int(ano)
                data_inicio = date(ano, mes, 1)
                data_fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
                context['data_filtrada'] = data_inicio
            except (ValueError, TypeError):
                pass

        # 4. Dados de população carcerária
        subquery_unidades = PopulacaoCarceraria.objects.filter(
            unidade=OuterRef('unidade'),
            **filtros
        )

        if data_inicio and data_fim:
            subquery_unidades = subquery_unidades.filter(
                data_atualizacao__range=(data_inicio, data_fim)
            )

        records_unidades = PopulacaoCarceraria.objects.filter(
            pk=Subquery(subquery_unidades.order_by('-data_atualizacao').values('pk')[:1])
        )

        unidades_data = [{'unidade': r.unidade.nome, 'total': r.total} for r in records_unidades]
        unidades_data.sort(key=lambda x: x['total'], reverse=True)

        # 5. Dados para gráficos
        context.update({
            'bar_labels': json.dumps([u['unidade'] for u in unidades_data]),
            'bar_values': json.dumps([u['total'] for u in unidades_data]),
            'total_populacao': sum(u['total'] for u in unidades_data),
            'internos_cadastrados': Interno.objects.count()
        })

        # 6. Dados REISP (sempre gerados)
        reisp_data = {}
        for r in records_unidades:
            reisp = r.unidade.reisp
            reisp_data[reisp] = reisp_data.get(reisp, 0) + r.total

        context.update({
            'bar_labels_reisp': json.dumps([f"{k}º REISP" for k in sorted(reisp_data)]),
            'bar_values_reisp': json.dumps([reisp_data[k] for k in sorted(reisp_data)])
        })

        # 7. Dados de servidores (com filtros aplicados)
        context.update({
            'total_servidores': Servidor.objects.filter(**filtros_servidor).count(),
            'total_servidores_ativos_policial_penal': Servidor.objects.filter(
                status=True,
                cargo='POLICIAL PENAL',
                **filtros_servidor
            ).count()
        })

        # 8. Opções de filtros
        context.update({
            'unidades': Unidade.objects.all().order_by('nome'),
            'meses': [(i, nome) for i, nome in enumerate(
                ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'], 1)],
            'anos': range(2020, date.today().year + 1),
            'filtro_unidade': unidade_id if unidade_id else 'todas',
            'filtro_mes': int(mes) if mes else None,
            'filtro_ano': int(ano) if ano else None
        })

        # 9. Dados adicionais
        context.update({
            'ticker_data': self.get_ticker_data(unidade_id, mes, ano)
        })
        context.update(self.get_historico_mensal(unidade_id, context.get('data_filtrada')))

        return context

    def get_ticker_data(self, unidade_id, mes, ano):
        filtros = {}
        if unidade_id and unidade_id != 'todas':
            filtros['unidade_id'] = unidade_id

        latest_date = PopulacaoCarceraria.objects.filter(**filtros).aggregate(Max('data_atualizacao'))[
            'data_atualizacao__max']
        if not latest_date:
            return []

        current_month_start = latest_date.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)

        unidades = Unidade.objects.filter(
            id=unidade_id) if unidade_id and unidade_id != 'todas' else Unidade.objects.all()

        ticker_data = []
        for unidade in unidades:
            atual = PopulacaoCarceraria.objects.filter(
                unidade=unidade,
                data_atualizacao__year=current_month_start.year,
                data_atualizacao__month=current_month_start.month
            ).order_by('-data_atualizacao').first()

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

        return sorted(ticker_data, key=lambda x: x['populacao'], reverse=True)

    def get_historico_mensal(self, unidade_id, data_referencia=None):
        meses_em_portugues = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }

        data_referencia = data_referencia or date.today()
        data_inicio = (data_referencia - relativedelta(months=11)).replace(day=1)

        filtros_historico = {}
        if unidade_id and unidade_id != 'todas':
            filtros_historico['unidade'] = unidade_id

        historico_completo = []
        for i in range(12):
            mes_ref = data_inicio + relativedelta(months=i)
            mes_inicio = mes_ref.replace(day=1)
            mes_fim = (mes_inicio + relativedelta(months=1))

            if unidade_id and unidade_id != 'todas':
                registro = PopulacaoCarceraria.objects.filter(
                    data_atualizacao__range=(mes_inicio, mes_fim),
                    **filtros_historico
                ).order_by('-data_atualizacao').first()
                total = registro.total if registro else 0
            else:
                subquery_unidades = PopulacaoCarceraria.objects.filter(
                    data_atualizacao__range=(mes_inicio, mes_fim),
                    unidade=OuterRef('unidade')
                ).order_by('-data_atualizacao')

                registros = PopulacaoCarceraria.objects.filter(
                    pk=Subquery(subquery_unidades.values('pk')[:1])
                )
                total = sum(r.total for r in registros) if registros else 0

            historico_completo.append({
                'mes': mes_ref,
                'total': total
            })

        bar_labels = [f"{meses_em_portugues[item['mes'].month]}/{item['mes'].year}" for item in historico_completo]
        bar_values = [item['total'] for item in historico_completo]

        return {
            'bar_labels_mensal': json.dumps(bar_labels),
            'bar_values_mensal': json.dumps(bar_values)
        }



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
