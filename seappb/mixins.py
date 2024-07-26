from django.views.generic.base import ContextMixin

class HideNavMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_nav'] = True
        return context