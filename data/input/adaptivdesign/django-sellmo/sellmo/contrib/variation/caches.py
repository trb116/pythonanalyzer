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

from sellmo.core import chaining
from sellmo.caching.caches import ChainCache
from sellmo.utils.query import PKIterator
from sellmo.apps.product.models import Product
from sellmo.apps.cart.forms import AddToCartForm
from sellmo.contrib.attribute.models import Attribute

from .signals import variations_invalidated
from .models import Variation, VariationQuerySet


class GroupVariationsCache(ChainCache):
    def __init__(self, *args, **kwargs):
        super(GroupVariationsCache, self).__init__(*args, **kwargs)
        variations_invalidated.connect(self._on_variations_invalidated)

    def _on_variations_invalidated(self, sender, product, **kwargs):
        self.delete(tags=self._tags(product=product))

    def _materialize(self, cache):

        # Reconstruct
        product_qs = Product.objects.all().polymorphic()

        grouped = []
        if cache:
            all_values = [group['value'] for group in cache]
            all_variants = [group['variant'] for group in cache]
            all_variants = list(PKIterator(product_qs, all_variants))
            attribute = Attribute.objects.get(pk=cache[0]['attribute'])

            model = attribute.get_type().get_model()
            if model:
                all_values = list(PKIterator(model, all_values))

            for group in cache:

                # Construct variations query
                variations = Variation.objects.all()
                variations.query = group['variations']

                # Get our slice
                value = all_values[0]
                all_values = all_values[1:]
                variant = all_variants[0]
                all_variants = all_variants[1:]

                grouped.append(
                    {
                        'attribute': attribute,
                        'value': value,
                        'variations': variations,
                        'variant': variant,
                    }
                )

        return grouped

    def _key(self, variations):
        # Should be safe, as long as I don't get eaten by a shark..
        return 'group_variations_%s' % hash(variations.query)

    def _tags(self, variations=None, product=None):
        if variations is None and product is None:
            raise TypeError()

        if variations is not None:
            products = variations.values_list('product', flat=True)
        else:
            products = [product.pk]

        return [
            'product_%s_variations' % product
            for product in products
        ]

    def catch(self, variations, **kwargs):
        # Attempt to get variations from cache
        cache = self.get(self._key(variations))
        if cache is not None:
            try:
                yield self._materialize(cache)
            except Exception as ex:
                # Cache must have been invalid, clear it.
                self.delete(self._key(variations))
            else:
                # Successfully materialized variations, stop all execution
                yield chaining.exit
                return

        # Continue with normal execution
        grouped = (yield chaining.forward).result

        cache = []
        if grouped is not None:
            for group in grouped:
                attribute = group['attribute']
                value = group['value']
                if attribute.get_type().get_model() is not None:
                    value = value.pk

                cache.append(
                    {
                        'attribute': attribute.pk,
                        'value': value,
                        'variations': group['variations'].query,
                        'variant': group['variant'].pk,
                    }
                )

        self.set(
            self._key(variations),
            cache,
            tags=self._tags(variations=variations)
        )


class VariationChoiceCache(ChainCache):

    def __init__(self, *args, **kwargs):
        super(VariationChoiceCache, self).__init__(*args, **kwargs)
        variations_invalidated.connect(self._on_variations_invalidated)

    def _on_variations_invalidated(self, sender, product, **kwargs):
        self.delete(tags=self._tags(product=product))

    def _key(self, variation):
        return 'variation_%s_choice' % variation.pk

    def _tags(self, variation=None, product=None):
        if variation is None and product is None:
            raise TypeError()
        if product is None:
            product = variation.product
        return ['product_%s_variation_choices' % product.pk]

    def catch(self, variation, **kwargs):
        cache = self.get(self._key(variation))
        if cache is not None:
            yield cache
            yield chaining.exit
            return

        # Continue with normal execution
        choice = (yield chaining.forward).result
        self.set(
            self._key(variation),
            choice,
            tags=self._tags(variation=variation)
        )


group_variations_cache = GroupVariationsCache(VariationQuerySet.group)
variation_choice_cache = VariationChoiceCache(AddToCartForm.variation_choice)
