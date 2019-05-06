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

from functools import partial

from sellmo.contrib.attribute.admin import BaseProductAttributeMixin

from django import forms
from django.forms import ValidationError
from django.forms.models import ModelForm
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils import six
from django.contrib.admin.sites import NotRegistered
from django.contrib.contenttypes.models import ContentType

from .forms import (
    VariantAttributeFormFactory, VariantAttributeFormMixin,
    ProductVariationFormFactory, ProductVariationFormMixin
)


class VariantAttributeMixin(BaseProductAttributeMixin):
    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = (
            self.get_attribute_formfactory(
                request,
                VariantAttributeFormFactory,
                prefix='attribute',
                mixin=VariantAttributeFormMixin,
                obj=obj,
                **kwargs
            ).factory()
        )
        return super(VariantAttributeMixin, self).get_form(
            request,
            obj=obj,
            **kwargs
        )

    def get_formset(self, request, obj=None, **kwargs):
        kwargs['form'] = (
            self.get_attribute_formfactory(
                request,
                VariantAttributeFormFactory,
                prefix='attribute',
                mixin=VariantAttributeFormMixin,
                obj=obj,
                **kwargs
            ).factory()
        )
        return super(VariantAttributeMixin, self).get_formset(
            request,
            obj=obj,
            **kwargs
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(VariantAttributeMixin, self).get_fieldsets(
            request, obj
        )
        fields = (
            self.get_attribute_formfactory(
                request,
                VariantAttributeFormFactory,
                prefix='attribute',
                mixin=VariantAttributeFormMixin,
                obj=obj
            ).get_attribute_formfield_names()
        )
        fieldsets += ((_("Attributes"), {'fields': fields}), )
        return fieldsets


class ProductVariationMixin(BaseProductAttributeMixin):
    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = (
            self.get_attribute_formfactory(
                request,
                ProductVariationFormFactory,
                prefix='variations',
                mixin=ProductVariationFormMixin,
                obj=obj,
                **kwargs
            ).factory()
        )
        return super(ProductVariationMixin, self).get_form(
            request,
            obj=obj,
            **kwargs
        )

    def save_model(self, request, obj, form, change):
        obj.save()
        form.save_variations()

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ProductVariationMixin, self).get_fieldsets(
            request, obj
        )
        fields = (
            self.get_attribute_formfactory(
                request,
                ProductVariationFormFactory,
                prefix='variations',
                mixin=ProductVariationFormMixin,
                obj=obj
            ).get_attribute_formfield_names()
        )
        fieldsets += ((_("Variations"), {'fields': fields}), )
        return fieldsets
