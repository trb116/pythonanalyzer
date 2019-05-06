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

from sellmo.core.loading import load

from django.db import models
from django.utils.translation import ugettext_lazy as _

import sellmo.apps.product as _product
import sellmo.contrib.product.subtypes.configurable_product as _configurable_product


@load(after='finalize_product_Product')
@load(action='finalize_product_ConfigurableProduct')
def finalize_model():
    class ConfigurableProduct(
        _configurable_product.models.ConfigurableProduct,
        _product.models.Product
    ):

        objects = _product.models.ProductManager.from_queryset(
            _product.models.ProductQuerySet)()

        class Meta(
            _configurable_product.models.ConfigurableProduct.Meta,
            _product.models.Product.Meta
        ):

            app_label = 'product'

    _configurable_product.models.ConfigurableProduct = ConfigurableProduct


class ConfigurableProduct(models.Model):

    is_configurable = True

    def get_options_tree(self, variations=None):

        if variations is None:
            variations = self.get_variations()

        # Variations are expected to be non grouped, thus a queryset
        # Before proceeding to custom form creation, check if we're dealing with a
        # variating product
        if variations is None or variations.count() == 0:
            return

        variations = variations.prefetch_related('values__attribute')

        # Get attributes which variate the current variations from eachother
        attributes = variations.get_variating_attributes()
        attributes = list(attributes)

        # Create valid value combinations
        all_combinations = {}
        for variation in variations:
            # We want to avoid querying, since we prefetched, convert
            # to list
            combination = [None] * len(attributes)
            for value in variation.values.all():
                if value.attribute in attributes:
                    idx = attributes.index(value.attribute)
                    combination[idx] = value
            all_combinations[tuple(combination)] = variation

        # Now that we have a 2d list structure of combinations, we can
        # create the option tree.
        def build_nodes(combination, combinations):

            options = []
            idx = len(combination)
            attribute = attributes[idx]

            values = set(el[0] for el in combinations)

            for value in values:
                new_combination = combination + (value, )
                if len(new_combination) < len(attributes):
                    nested_combinations = [
                        el[1:] for el in combinations if el[0] == value
                    ]

                    nested = build_nodes(new_combination, nested_combinations)
                    options.append([value, nested])
                else:
                    options.append([value, all_combinations[new_combination]])

            return options

        nodes = build_nodes(tuple(), all_combinations.keys())
        return {'attributes': attributes, 'nodes': nodes}

    class Meta:
        abstract = True
        verbose_name = _("configurable product")
        verbose_name_plural = _("configurable products")
