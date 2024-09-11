from django.shortcuts import render, redirect
from .models import Gesipe_adm
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.utils.timezone import now
from .forms import GesipeAdmForm
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q  # Para pesquisas com OR lógico
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from datetime import datetime, date


# Create your views here.

# url - view - html


class Gesipe(LoginRequiredMixin, ListView):
    template_name = "gesipe.html"
    model = Gesipe_adm
    paginate_by = 5
    ordering = ['data']

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        queryset = super().get_queryset()

        if query:
            queryset = queryset.filter(
                Q(usuario__username__icontains=query) |
                Q(data__icontains=query) |
                Q(total__icontains=query)
            )

        return queryset

    def post(self, request, *args, **kwargs):
        data_pesquisa = request.POST.get('data_pesquisa')
        if data_pesquisa:
            try:
                data_pesquisa = datetime.strptime(data_pesquisa, "%Y-%m-%d").date()
            except ValueError:
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
        return context


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
        dados_adm = form.save(commit=False)
        dados_adm.data_edicao = timezone.now()  # Atualiza a data de edição
        dados_adm.save()

        messages.success(self.request, 'Dados atualizados com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formatted_date'] = self.object.data.strftime('%d/%m/%Y')
        return context


