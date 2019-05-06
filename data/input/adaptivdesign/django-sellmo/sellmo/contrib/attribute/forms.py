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

from sellmo.utils.forms import FormFactory

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Attribute


class ProductAttributeFormMixin(object):
    def __init__(self, *args, **kwargs):
        initial = {}
        if 'initial' in kwargs:
            initial = kwargs['initial']
        instance = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
        if instance:
            for attribute in self.__attributes:
                if attribute in instance.attributes:
                    field_name = self.__attribute_field_names[attribute.key]
                    field = self.__attribute_fields[attribute.key]
                    value = instance.attributes[attribute]
                    initial[field_name] = value

        kwargs['initial'] = initial
        super(ProductAttributeFormMixin, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(ProductAttributeFormMixin, self).save(commit=False)
        for attribute in self.__attributes:
            field_name = self.__attribute_field_names[attribute.key]
            value = self.cleaned_data.get(field_name)
            instance.attributes[attribute.key] = value
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProductAttributeFormFactory(FormFactory):
    def __init__(
        self,
        form=None,
        mixin=None,
        prefix=None,
        attribute_set=None,
        formfield_callback=None
    ):
        self.form = form or forms.ModelForm
        self.mixin = mixin or ProductAttributeFormMixin
        self.prefix = prefix
        self.attribute_set = attribute_set
        self.formfield_callback = formfield_callback

    def get_attributes(self):
        attributes = Attribute.objects.all()
        if self.attribute_set is not None:
            attributes = (
                attributes.for_attribute_set(self.attribute_set)
                | attributes.filter(sets=None)
            )
        else:
            attributes = attributes.filter(sets=None)
        return attributes

    def get_attribute_formfield_names(self):
        keys = self.get_attributes().values_list('key', flat=True)
        names = []
        for key in keys:
            if self.prefix:
                names.append('%s_%s' % (self.prefix, key))
            else:
                names.append(key)
        return names

    def get_attribute_formfield_name(self, attribute):
        if self.prefix:
            return '%s_%s' % (self.prefix, attribute.key)
        else:
            return attribute.key

    def get_attribute_formfield(self, attribute):
        typ = attribute.get_type()
        choices = typ.get_choices(attribute)
        if choices is not None and not attribute.required:
            choices = [(typ.get_empty_value(), '---------')] + choices

        field_cls, args, kwargs = typ.get_formfield(
            label=attribute.name,
            required=attribute.required,
            choices=choices
        )
        formfield = field_cls(*args, **kwargs)
        return formfield

    def factory(self):
        attributes = self.get_attributes()
        names = {}
        fields = {}
        attr_dict = {
            '_{0}__attributes'.format(self.mixin.__name__): attributes,
            '_{0}__attribute_field_names'.format(self.mixin.__name__): names,
            '_{0}__attribute_fields'.format(self.mixin.__name__): fields,
        }
        for attribute in attributes:
            formfield = self.get_attribute_formfield(attribute)
            if self.formfield_callback:
                formfield = self.formfield_callback(attribute, formfield)
            name = self.get_attribute_formfield_name(attribute)
            names[attribute.key] = name
            fields[attribute.key] = formfield
            attr_dict[name] = formfield

        return type('ProductAttributeForm', (self.mixin, self.form), attr_dict)
