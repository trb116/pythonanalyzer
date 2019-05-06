from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, ListView, TemplateView

import autocomplete_light

from aristotle_mdr.utils import get_concepts_for_apps
from aristotle_mdr.models import _concept


class GenericAlterManyToManyView(FormView):
    model_to_add = None
    model_base = None
    template_name = "aristotle_mdr/generic/actions/alter_many_to_many.html"
    model_base_field = None

    def get_context_data(self, **kwargs):
        context = super(GenericAlterManyToManyView, self).get_context_data(**kwargs)
        context['model_to_add'] = self.model_to_add
        context['model_base'] = self.model_base
        context['item'] = self.item
        context['submit_url'] = self.request.get_full_path()
        return context

    def dispatch(self, request, *args, **kwargs):
        self.item = self.model_base.objects.get(id=self.kwargs['iid'])
        return super(GenericAlterManyToManyView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.item.get_absolute_url()

    def get_form_class(self):
        class M2MForm(forms.Form):
            items_to_add = forms.ModelMultipleChoiceField(
                queryset=self.model_to_add.objects.visible(self.request.user),
                label="Attach",
                required=False,
                widget=autocomplete_light.MultipleChoiceWidget(
                    self.model_to_add.get_autocomplete_name()
                ),
            )
        return M2MForm

    def get_initial(self):
        return {
            'items_to_add': getattr(self.item, self.model_base_field).all()
        }

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.item.__setattr__(self.model_base_field, form.cleaned_data['items_to_add'])
        self.item.save()
        return HttpResponseRedirect(self.get_success_url())
