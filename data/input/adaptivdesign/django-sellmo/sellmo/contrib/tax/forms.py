# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import ProductTaxClass


class ProductTaxClassesForm(forms.ModelForm):

    tax_classes = forms.ModelMultipleChoiceField(
        queryset=ProductTaxClass.objects.all(),
        required=False,
        label=_("tax classes")
    )

    def __init__(self, *args, **kwargs):
        super(ProductTaxClassesForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields[
                'tax_classes'].initial = self.instance.relatable_tax_producttaxclass.all(
                )

    def save(self, commit=True):
        product = super(ProductTaxClassesForm, self).save(commit=False)

        _save_m2m = getattr(self, 'save_m2m', None)

        def save_m2m():
            if _save_m2m:
                _save_m2m()
            product.relatable_tax_producttaxclass = self.cleaned_data[
                'tax_classes'
            ]

        if commit:
            product.save()
            save_m2m()
        else:
            self.save_m2m = save_m2m
        return product
