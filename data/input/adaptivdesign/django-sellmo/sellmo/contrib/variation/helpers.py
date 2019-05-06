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

from sellmo.utils.text import underscore_concat
from sellmo.contrib.attribute.helpers import (
    ProductAttributeHelper as _ProductAttributeHelper
)
from sellmo.contrib.attribute.helpers import AttributeHelper

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst
from django.utils import six

import sellmo.contrib.attribute as _attribute


def differs_field_name(field_name):
    return underscore_concat(field_name, 'differs')


class ProductAttributeHelper(_ProductAttributeHelper):
    def get_values_queryset(self):
        values = super(ProductAttributeHelper, self).get_values_queryset()
        values = values.filter(variates=False)
        return values

    def get_new_value(self):
        value = super(ProductAttributeHelper, self).get_new_value()
        value.variates = False
        return value


class VariantAttributeHelper(ProductAttributeHelper):
    def get_values(self):
        variant_values = {
            value.attribute.key: value
            for value in super(VariantAttributeHelper, self).get_values()
        }

        product_values = {
            value.attribute.key: value
            for value in self._product.product.attributes.get_values()
        }

        # Return a combination of product values and variant values
        # where variant values override product values
        return list(six.itervalues(dict(product_values, **variant_values)))

    def get_value(self, key):
        value = super(VariantAttributeHelper, self).get_value(key)
        if value is None:
            value = self._product.product.attributes.get_value(key)
        return value

    def set_value_value(self, key, value_value):
        attribute = self.get_attribute(key)
        product_value = self._product.product.attributes.get_value(key)
        variant_value = self.get_own_value(key)
        if (
            not attribute.variates and product_value is not None and
            product_value.value == value_value
        ):
            if variant_value:
                # Make sure we don't set this value
                variant_value.value = None
        else:
            # We don't need to inherit from product value, continue
            # original behaviour
            super(VariantAttributeHelper, self).set_value_value(
                key, value_value
            )


class VariationAttributeHelper(AttributeHelper):
    def __init__(self, variation):
        super(VariationAttributeHelper, self).__init__()
        self._variation = variation

    @cached_property
    def _product(self):
        if hasattr(self._variation, 'product'):
            return self._variation.product.downcast()

    def get_values(self):
        variation_values = {
            value.attribute.key: value
            for value in self._variation.values.all()
        }

        variant_values = {}
        if self._product:
            variant_values = {
                value.attribute.key: value
                for value in self._product.attributes.get_values()
            }

        # Return a combination of variant values and variation values
        # where variation values override variant values
        return list(six.itervalues(dict(variant_values, **variation_values)))

    def get_value(self, key):
        attribute = self.get_attribute(key)
        value = None
        try:
            value = self._variation.values.get(attribute=attribute)
        except _attribute.models.Value.DoesNotExist:
            if self._product:
                value = self._product.attributes.get_value(key)

        return value
