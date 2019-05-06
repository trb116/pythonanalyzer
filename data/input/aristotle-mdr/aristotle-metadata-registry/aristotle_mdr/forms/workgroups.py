import autocomplete_light

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

import aristotle_mdr.models as MDR


class AddMembers(forms.Form):
    roles = forms.MultipleChoiceField(
        label=_("Workgroup roles"),
        choices=sorted(MDR.Workgroup.roles.items()),
        widget=forms.CheckboxSelectMultiple
    )
    users = forms.ModelMultipleChoiceField(
        label=_("Select users"),
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('Autocomplete_AristotleUser')
    )

    def clean_roles(self):
        roles = self.cleaned_data['roles']
        roles = [role for role in roles if role in MDR.Workgroup.roles.keys()]
        return roles
