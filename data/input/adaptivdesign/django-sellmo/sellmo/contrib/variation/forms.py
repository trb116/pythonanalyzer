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
from django.forms import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.validators import EMPTY_VALUES

from sellmo.apps.purchase.exceptions import PurchaseInvalid
from sellmo.contrib.attribute.forms import ProductAttributeFormFactory
from sellmo.contrib.attribute.models import Value

from .utils import values_slug

import sellmo.apps.product as _product
import sellmo.contrib.attribute as _attribute


class SaveFieldMixin(object):
    def get_invalidated_values(self, product, attribute, values):
        field = '{0}__in'.format(attribute.get_type().get_value_field_name())
        kwargs = {field: values}

        q = ~Q(**kwargs)

        return _attribute.models.Value.objects.filter(
            attribute=attribute,
            product=product,
            variates=True
        ).filter(q)

    def get_existing_values(self, product, attribute, values):
        field = '{0}__in'.format(attribute.get_type().get_value_field_name())
        kwargs = {field: values}

        q = Q(**kwargs)

        return Value.objects.filter(
            attribute=attribute,
            product=product,
            variates=True
        ).filter(q)

    def save(self, product, attribute, values=None):
        # Make sure values is an iterable
        values = values or []
        invalidated = self.get_invalidated_values(product, attribute, values)
        invalidated.delete()

        existing = [
            value.get_value()
            for value in self.get_existing_values(
                product, attribute, values
            )
        ]
        for value in values:
            if not value in existing:
                obj = Value(
                    product=product,
                    variates=True,
                    attribute=attribute
                )
                obj.set_value(value)
                obj.save()


class SeperatedInputField(forms.Field, SaveFieldMixin):
    def __init__(self, field, seperator=u'|', **kwargs):
        super(SeperatedInputField, self).__init__(**kwargs)
        self._field = field(**kwargs)
        self._seperator = seperator

    def from_values(self, values):
        return self._seperator.join(
            [unicode(value.get_value()) for value in values]
        )

    def to_python(self, value):
        result = []
        value = super(SeperatedInputField, self).to_python(value)
        if value in EMPTY_VALUES:
            return result
        values = value.split(self._seperator)
        for value in values:
            result.append(self._field.clean(value))

        return result


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField, SaveFieldMixin):
    def from_values(self, values):
        return self.queryset.filter(
            pk__in=[value.get_value().pk for value in values]
        )


class MultipleChoiceField(forms.MultipleChoiceField, SaveFieldMixin):
    def from_values(self, values):
        return [unicode(value.get_value()) for value in values]


class TypedMultipleChoiceField(forms.TypedMultipleChoiceField, SaveFieldMixin):
    def from_values(self, values):
        return [unicode(value.get_value()) for value in values]


class VariantAttributeFormFactory(ProductAttributeFormFactory):
    def get_attribute_formfield(self, attribute):
        typ = attribute.get_type()
        choices = typ.get_choices(attribute)
        if choices is not None:
            # Always allow blank
            choices = [(typ.get_empty_value(), '---------')] + choices

        if attribute.variates:
            label = _("{attribute} (variates)").format(
                attribute=attribute.name
            )
        else:
            label = attribute.name
        field_cls, args, kwargs = typ.get_formfield(
            label=label,
            required=attribute.required,
            choices=choices
        )
        return field_cls(*args, **kwargs)


class ProductVariationFormFactory(ProductAttributeFormFactory):
    def get_attributes(self):
        attributes = super(ProductVariationFormFactory, self).get_attributes()
        return attributes.filter(variates=True)

    def get_attribute_formfield(self, attribute):
        typ = attribute.get_type()
        choices = typ.get_choices(attribute)
        field_cls, args, kwargs = typ.get_formfield(
            label=attribute.name,
            required=False,
            choices=choices
        )

        if field_cls is forms.ModelChoiceField:
            field_cls = ModelMultipleChoiceField
        elif field_cls is forms.ChoiceField:
            field_cls = MultipleChoiceField
        elif field_cls is forms.TypedChoiceField:
            field_cls = TypedMultipleChoiceField
        else:
            args = [field_cls] + args
            field_cls = SeperatedInputField

        return field_cls(*args, **kwargs)


class ProductVariationFormMixin(object):
    def __init__(self, *args, **kwargs):
        initial = {}
        if 'initial' in kwargs:
            initial = kwargs['initial']
        instance = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
        if instance:
            initial.update(
                {
                    self.__attribute_field_names[key]: value
                    for key, value in self.__get_values(instance).iteritems()
                }
            )
        kwargs['initial'] = initial
        super(ProductVariationFormMixin, self).__init__(*args, **kwargs)

    def __get_values(self, product):
        result = {}
        for attribute in self.__attributes:
            if product.pk is not None:
                try:
                    values = Value.objects.filter(
                        attribute=attribute,
                        product=product,
                        variates=True
                    )
                except Value.DoesNotExist:
                    values = None
            else:
                values = None

            field = self.__attribute_fields[attribute.key]
            result[attribute.key] = field.from_values(values)
        return result

    def save(self, commit=True):
        instance = super(ProductVariationFormMixin, self).save(commit=False)

        def save_variations():
            for attribute in self.__attributes:
                values = self.cleaned_data.get(
                    self.__attribute_field_names[attribute.key]
                )
                field = self.__attribute_fields[attribute.key]
                field.save(instance, attribute, values)

        if commit:
            instance.save()
            self.save_m2m()
            save_variations()
        else:
            self.save_variations = save_variations
        return instance


class VariantAttributeFormMixin(object):
    def __init__(self, *args, **kwargs):
        initial = {}
        if 'initial' in kwargs:
            initial = kwargs['initial']
        instance = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
        if instance:
            initial.update(
                {
                    self.__attribute_field_names[
                        attribute.key
                    ]: instance.attributes[attribute]
                    for attribute in self.__attributes
                    if attribute in instance.attributes
                }
            )
        kwargs['initial'] = initial
        super(VariantAttributeFormMixin, self).__init__(*args, **kwargs)
        for field in self.fields:
            self[field].field.required = False

    def save(self, commit=True):
        instance = super(VariantAttributeFormMixin, self).save(commit=False)
        instance.product = self.cleaned_data['product']
        for attribute in self.__attributes:
            value = self.cleaned_data.get(
                self.__attribute_field_names[attribute.key]
            )
            instance.attributes[attribute.key] = value
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def clean(self):
        cleaned_data = super(VariantAttributeFormMixin, self).clean()
        product = cleaned_data['product']

        # Temporary collect values to generate slug
        # Get only the values which variate
        values = []
        product_values = []

        for attribute in self.__attributes.filter(variates=True):
            value = Value(attribute=attribute)
            value.value = cleaned_data.get(
                self.__attribute_field_names[attribute.key]
            )
            if not value.is_empty():
                # At this point make sure product doesn't have the same value
                if product.attributes[attribute.key] == value.value:
                    product_values.append(value)
                values.append(value)

        # Make sure we don't define the same values as the parent product
        if len(product_values) == len(values):
            raise ValidationError(
                _("This variant does not differ from it's parent product.")
            )

        # Enforce at least one variated value
        if not values:
            raise ValidationError(
                _("A variant requires at least one variated attribute.")
            )

        # Generate slug if needed
        if cleaned_data.has_key('slug'):
            if not cleaned_data['slug']:
                cleaned_data['slug'] = values_slug(
                    values,
                    prefix=cleaned_data['product'].slug
                )

            self.data[self.add_prefix('slug')] = cleaned_data['slug']

        return cleaned_data
