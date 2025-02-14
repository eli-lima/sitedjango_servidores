from django.shortcuts import render, redirect
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import (Apreensao, TipoOcorrencia, Atendimento, Ocorrencia,
                     Custodia, Mp)
from interno.models import Interno
from .forms import (ApreensaoForm, OcorrenciaForm, AtendimentoForm,
                    Objeto, Natureza, CustodiaForm,CustodiaEditForm,
                    MpForm)
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Count
from django.contrib.auth.mixins import UserPassesTestMixin
from .utils import calculate_bar_chart, calculate_pie_apreensao
from datetime import date
from django.db.models import Q



# Create your views here.
def buscar_interno(request):
    query = request.GET.get('interno_nome', '').strip()

    if len(query) < 3:  # Só busca se o termo tiver mais de 3 caracteres
        internos = []
    else:
        # Busca pelo nome, CPF, prontuário ou nome da mãe
        internos = Interno.objects.filter(
            Q(nome__icontains=query) |
            Q(cpf__icontains=query) |
            Q(prontuario__icontains=query) |
            Q(nome_mae__icontains=query)
        ).order_by('nome')[:10]  # Limite de 10 resultados

    return render(request, 'partials/interno_tabela.html', {'internos': internos})




def buscar_interno(request):
    query = request.GET.get('interno_nome', '').strip()
    if len(query) < 3:  # Só busca se o termo tiver mais de 3 caracteres
        internos = []
    else:
        internos = Interno.objects.filter(nome__icontains=query).order_by('nome')[:10]  # Limite de resultados



    return render(request, 'partials/interno_tabela.html', {'internos': internos})





class Copen(LoginRequiredMixin, TemplateView, UserPassesTestMixin):
    template_name = "copen.html"

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obter o mês e o ano atuais
        hoje = now()
        mes_atual = hoje.month
        ano_atual = hoje.year

        # Filtrar os atendimentos realizados no mês atual
        lista_atendimento_mes = Atendimento.objects.filter(
            data__year=ano_atual,
            data__month=mes_atual
        )

        # Contar os atendimentos realizados no mês
        atendimento_mes = lista_atendimento_mes.count()

        context['lista_atendimento_mes'] = lista_atendimento_mes
        context['atendimento_mes'] = atendimento_mes



        # Filtrar as apreensoes realizados no mês atual
        lista_apreensao_mes = Apreensao.objects.filter(
            data__year=ano_atual,
            data__month=mes_atual
        )

        # Contar os atendimentos realizados no mês
        apreensao_mes = lista_apreensao_mes.count()

        context['lista_apreensao_mes'] = lista_apreensao_mes
        context['apreensao_mes'] = apreensao_mes

        # Filtrar os ocorrencia realizados no mês atual
        lista_ocorrencia_mes = Ocorrencia.objects.filter(
            data__year=ano_atual,
            data__month=mes_atual
        )

        # Contar os ocorrencia realizados no mês
        ocorrencia_mes = lista_ocorrencia_mes.count()
        print(f'ocorrencias do mes: {ocorrencia_mes}')

        context['lista_ocorrencia_mes'] = lista_ocorrencia_mes
        context['ocorrencia_mes'] = ocorrencia_mes

        # somar custodias ativas
        lista_custodias_ativas = Custodia.objects.filter(data_saida__isnull=True)
        print(f'custodias ativas: {lista_custodias_ativas}')
        custodias_ativas = lista_custodias_ativas.count()
        context['lista_custodias_ativas'] = lista_custodias_ativas
        context['custodias_ativas'] = custodias_ativas
        print(custodias_ativas)

        # Filtrar os mp realizados no mês atual
        lista_mp_mes = Mp.objects.filter(
            data_cumprimento__year=ano_atual,
            data_cumprimento__month=mes_atual
        )

        # Contar os mp realizados no mês
        mp_mes = lista_mp_mes.count()

        context['lista_mp_mes'] = lista_mp_mes
        context['mp_mes'] = mp_mes


        # graficos
        #grafico de barra mensal

        # Dicionário com os nomes dos meses
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

        # Lista de anos disponíveis (últimos 5 anos e o atual)
        current_year = now().year
        anos = list(range(current_year - 5, current_year + 1))
        # Filtrar os registros para o mês específico

        apreensoes = Apreensao.objects.all()

        print(F'TOTAL MENSAL ATUAL: {apreensoes}')

        # Chamar a função para calcular os dados do gráfico
        monthly_totals_apreensao, monthly_labels_apreensao = calculate_bar_chart(apreensoes ,ano_atual, mes_atual)

        print(monthly_totals_apreensao)
        print(f'labels do meses: {monthly_labels_apreensao}')
        # Captura os valores de ano e mês enviados pelo formulário de filtro
        # ano_selecionado = self.request.GET.get('ano', timezone.now().year)
        # mes_selecionado = self.request.GET.get('mes', timezone.now().month)


        # Certifique-se de converter para `int` para usá-los em consultas e lógica
        ano_selecionado = int(ano_atual)
        mes_selecionado = int(mes_atual)


        #grafico pizza apreensoes
        # Chamar a função para calcular os dados do gráfico de pizza
        pie_labels_apreensao, pie_values_apreensao = calculate_pie_apreensao()
        print(f'pie {pie_values_apreensao}')
        print(f'label: {pie_labels_apreensao}')

        # Atualizar o contexto com os filtros
        context.update({
            'monthly_totals_apreensao': monthly_totals_apreensao,
            'monthly_labels_apreensao': monthly_labels_apreensao,
            'meses': meses,
            'anos': anos,
            'ano_selecionado': ano_selecionado,
            'mes_selecionado': mes_selecionado,
            'pie_labels_apreensao': pie_labels_apreensao,
            'pie_values_apreensao': pie_values_apreensao,
        })

        # grafico pizza apreensao

        return context


class ApreensaoAddView(LoginRequiredMixin, FormView, UserPassesTestMixin):
    form_class = ApreensaoForm
    template_name = 'copen_apreensao_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['naturezas'] = Natureza.objects.all()  # Passa as naturezas para o template
        return context

    def form_valid(self, form):
        apreensao = form.save(commit=False)
        apreensao.usuario = self.request.user
        apreensao.data_edicao = timezone.now()
        apreensao.save()
        messages.success(self.request, 'Apreensão registrada com sucesso!')
        return redirect(self.success_url)


class AtendimentoView(LoginRequiredMixin, FormView, UserPassesTestMixin):
    form_class = AtendimentoForm
    template_name = 'copen_atendimento_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        atendimento = form.save(commit=False)
        atendimento.usuario = self.request.user
        atendimento.data_edicao = timezone.now()
        atendimento.save()
        messages.success(self.request, 'Atendimento registrado com sucesso!')
        return redirect(self.success_url)


class OcorrenciaView(FormView, LoginRequiredMixin, UserPassesTestMixin):
    form_class = OcorrenciaForm
    template_name = 'copen_ocorrencia_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        # Captura o ID do interno enviado pelo campo oculto
        interno_id = self.request.POST.get('interno_id')
        print(f"ID do interno capturado: {interno_id}")  # Debug: ID do interno

        try:
            # Verifica se o ID do interno é válido
            interno = Interno.objects.get(id=interno_id)
            print(f"Interno encontrado no banco de dados: {interno}")  # Debug: Interno encontrado

            # Cria a ocorrência
            ocorrencia = form.save(commit=False)
            print("Instância de Ocorrencia criada a partir do formulário.")  # Debug: Instância criada

            ocorrencia.usuario = self.request.user
            print(f"Usuário associado à ocorrência: {self.request.user}")  # Debug: Usuário associado

            ocorrencia.interno = interno  # Define o interno encontrado
            print(f"Interno associado à ocorrência: {interno}")  # Debug: Interno associado

            ocorrencia.data_edicao = timezone.now()
            ocorrencia.save()
            print("Ocorrência salva no banco de dados.")  # Debug: Ocorrência salva

            messages.success(self.request, 'Ocorrência salva com sucesso!')
            return redirect(self.success_url)

        except Interno.DoesNotExist:
            print(f"Erro: Interno com ID '{interno_id}' não encontrado.")  # Debug: Interno não encontrado
            messages.error(self.request, f"Erro: Interno não encontrado. Verifique os dados.")
            return self.form_invalid(form)

        except Exception as e:
            print(f"Erro ao salvar a ocorrência: {e}")  # Debug: Captura qualquer erro
            messages.error(self.request, "Erro ao salvar a ocorrência. Verifique os dados e tente novamente.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("Preparando o contexto para o template.")  # Debug: Contexto sendo preparado
        context['tipo_objeto'] = TipoOcorrencia.objects.all()
        print(f"Tipos de ocorrência disponíveis: {context['tipo_objeto']}")  # Debug: Tipos carregados
        return context

    def form_invalid(self, form):
        print("Formulário inválido.")  # Debug: Validação falhou
        print(f"Erros do formulário: {form.errors}")  # Debug: Exibe os erros do formulário
        return super().form_invalid(form)


class CustodiaAddView(FormView, LoginRequiredMixin, UserPassesTestMixin):
    form_class = CustodiaForm
    template_name = 'copen_custodia_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        # Captura o ID do interno enviado pelo campo oculto
        interno_id = self.request.POST.get('interno_id')
        print(f"ID do interno capturado: {interno_id}")  # Debug: ID do interno

        try:
            # Verifica se o ID do interno é válido
            interno = Interno.objects.get(id=interno_id)
            print(f"Interno encontrado no banco de dados: {interno}")  # Debug: Interno encontrado

            # Cria a ocorrência
            custodia = form.save(commit=False)
            print("Instância de custodia criada a partir do formulário.")  # Debug: Instância criada

            custodia.usuario = self.request.user
            print(f"Usuário associado à custodia: {self.request.user}")  # Debug: Usuário associado

            custodia.interno = interno  # Define o interno encontrado
            print(f"Interno associado à custodia: {interno}")  # Debug: Interno associado

            custodia.data_edicao = timezone.now()
            custodia.save()
            print("Custodia salva no banco de dados.")  # Debug: Ocorrência salva

            messages.success(self.request, 'Custódia salva com sucesso!')
            return redirect(self.success_url)

        except Interno.DoesNotExist:
            print(f"Erro: Interno com ID '{interno_id}' não encontrado.")  # Debug: Interno não encontrado
            messages.error(self.request, f"Erro: Interno não encontrado. Verifique os dados.")
            return self.form_invalid(form)

        except Exception as e:
            print(f"Erro ao salvar a ocorrência: {e}")  # Debug: Captura qualquer erro
            messages.error(self.request, "Erro ao salvar a custodia. Verifique os dados e tente novamente.")
            return self.form_invalid(form)


class CustodiaEditView(UpdateView, LoginRequiredMixin, UserPassesTestMixin):
    model = Custodia
    form_class = CustodiaEditForm
    template_name = 'copen_custodia_edit.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        custodia = form.save(commit=False)
        custodia.data_edicao = now()  # Atualiza a data de edição
        custodia.save()
        messages.success(self.request, 'Data de saída salva com sucesso!')
        return redirect (self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['custodia'] = self.get_object()
        return context

    def form_invalid(self, form):
        print("Formulário inválido:", form.errors)  # Depuração
        messages.error(self.request, 'Erro ao salvar o formulário.')
        return super().form_invalid(form)


# view mandado de prisao

class MpAddView(FormView, LoginRequiredMixin, UserPassesTestMixin):
    form_class = MpForm
    template_name = 'copen_mp_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        # Captura o ID do interno enviado pelo campo oculto
        interno_id = self.request.POST.get('interno_id')
        print(f"ID do interno capturado: {interno_id}")  # Debug: ID do interno

        try:
            # Verifica se o ID do interno é válido
            interno = Interno.objects.get(id=interno_id)
            print(f"Interno encontrado no banco de dados: {interno}")  # Debug: Interno encontrado

            # Cria a ocorrência
            mp = form.save(commit=False)
            print("Instância de mp criada a partir do formulário.")  # Debug: Instância criada

            mp.usuario = self.request.user
            print(f"Usuário associado à mp: {self.request.user}")  # Debug: Usuário associado

            mp.interno = interno  # Define o interno encontrado
            print(f"Interno associado à mp: {interno}")  # Debug: Interno associado

            mp.data_edicao = timezone.now()
            mp.save()
            print("mp salva no banco de dados.")  # Debug: Ocorrência salva

            messages.success(self.request, 'Mandado de Prisão salvo com sucesso!')
            return redirect(self.success_url)

        except Interno.DoesNotExist:
            print(f"Erro: Interno com ID '{interno_id}' não encontrado.")  # Debug: Interno não encontrado
            messages.error(self.request, f"Erro: Interno não encontrado. Verifique os dados.")
            return self.form_invalid(form)

        except Exception as e:
            print(f"Erro ao salvar a ocorrência: {e}")  # Debug: Captura qualquer erro
            messages.error(self.request, "Erro ao salvar a custodia. Verifique os dados e tente novamente.")
            return self.form_invalid(form)