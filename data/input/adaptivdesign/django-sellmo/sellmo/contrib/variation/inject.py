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
from django.db import models
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sellmo.core import chaining
from sellmo.core.loading import load
from sellmo.core import indexing
from sellmo.apps.pricing import Price
from sellmo.contrib.attribute.query import product_q
from sellmo.utils.text import call_or_format

import sellmo.apps.purchase as _purchase
import sellmo.apps.product as _product
import sellmo.apps.cart as _cart
import sellmo.contrib.attribute as _attribute
import sellmo.contrib.variation as _variation

from .helpers import ProductAttributeHelper
from .constants import VARIATION_CHOICE_FORMAT, VARIATION_VALUE_SEPERATOR


class AddToCartForm(_cart.forms.AddToCartForm):

    @classmethod
    @chaining.define
    def variation_choice(cls, variation, attributes=None, **kwargs):

        result = (yield chaining.forward).result
        if result is not None:
            return

        variant = variation.variant.downcast()
        price_adjustment = None

        if variant.is_variant:
            a = Price.calculate(product=variant, raw=True)
            b = Price.calculate(product=variant.product, raw=True)

            price_adjustment = Price(0)
            if a is not None and b is not None:
                price_adjustment = (a - b)

        values = variation.values.all().order_by('attribute')
        if attributes is not None:
            values = values.filter(attribute__in=attributes)

        values = VARIATION_VALUE_SEPERATOR.join(
            [unicode(value) for value in values]
        )

        yield call_or_format(
            VARIATION_CHOICE_FORMAT,
            variation=variation,
            variant=variant,
            values=values,
            price_adjustment=price_adjustment
        )

    @classmethod
    def factory(
        cls,
        data=None,
        product=None,
        variations=None,
        hide_variation_field=False,
        **kwargs
    ):

        Form = super(AddToCartForm, cls).factory(
            data=data,
            product=product,
            variations=variations,
            hide_variation_field=hide_variation_field,
            **kwargs
        )

        if variations is None:
            if data is not None and 'variations' in data:
                keys = data['variations'].split('|')
                variations = _variation.models.Variation.objects.filter(
                    pk__in=keys)
            elif product is not None:
                variations = product.get_variations()

        # Before proceeding to custom form creation, check if we're dealing with a
        # variating product
        if variations is None or variations.count() == 0:
            return AddToCartForm

        if not hide_variation_field:
            # Get attributes which variate the current variations
            # from eachother
            attributes = _attribute.models.Attribute.objects.which_variate_variations(
                variations)

            # See if a single attribute is used across all variations
            if attributes is not None and attributes.count() == 1:
                # Label equals attribute name
                label = unicode(attributes[0])
            else:
                # Can't make up a specific label
                label = _("Variation")

        attrs = {
            'variations': forms.CharField(
                initial='|'.join(
                    [
                        variation.pk for variation in variations
                    ]
                ),
                widget=forms.HiddenInput
            )
        }

        if not hide_variation_field:
            attrs['variation'] = forms.ChoiceField(
                initial=variations[:1][0].pk,
                label=label,
                choices=[
                    (
                        obj.id, AddToCartForm.variation_choice(
                            obj, attributes
                        )
                    ) for obj in variations
                ]
            )
        else:
            attrs['variation'] = forms.CharField(
                initial=variations[:1][0].pk,
                widget=forms.HiddenInput
            )
        Form = type('AddToCartForm', (AddVariationToCartForm, Form), attrs)
        return Form


class AddVariationToCartForm(forms.Form):
    def get_purchase_args(self):
        args = super(AddVariationToCartForm, self).get_purchase_args()
        try:
            variation = _variation.models.Variation.objects.get(
                pk=self.cleaned_data['variation']
            )
        except _variation.models.Variation.DoesNotExist:
            raise PurchaseInvalid()

        args['product'] = variation.variant.downcast()
        args['variation'] = variation
        return args


_cart.forms.AddToCartForm = AddToCartForm


@load(before='finalize_purchase_Purchase')
def load_model():

    class Purchase(_purchase.models.Purchase):

        @classmethod
        def factory(cls, variation=None, **kwargs):
            if variation is not None:
                return _variation.models.VariationPurchase
            return super(Purchase, cls).factory(variation=variation, **kwargs)

        class Meta(_purchase.models.Purchase.Meta):
            abstract = True

    class PurchaseQuerySet(_purchase.models.PurchaseQuerySet):
        def mergeable_with(self, purchase):
            purchase = purchase.downcast()
            queryset = self
            if isinstance(purchase, _variation.models.VariationPurchase):
                queryset = queryset.filter(
                    productpurchase__variationpurchase__variation_key=
                    purchase.variation_key
                )
            queryset = super(PurchaseQuerySet,
                             queryset).mergeable_with(purchase)

            return queryset

    _purchase.models.Purchase = Purchase
    _purchase.models.PurchaseQuerySet = PurchaseQuerySet


@load(before='finalize_product_Product')
def load_model():
    class ProductQuerySet(_product.models.ProductQuerySet):
        def variants(self, exclude=False):
            content_types = ContentType.objects.get_for_models(
                *_variation.models.Variant.SUBTYPES)
            content_types = content_types.values()

            if exclude:
                queryset = self.exclude(content_type__in=content_types)
            else:
                queryset = self.filter(content_type__in=content_types)

            return queryset

    class Product(_product.models.Product):

        is_variant = False

        variations_synced = models.BooleanField(default=False, editable=False)

        def __init__(self, *args, **kwargs):
            super(Product, self).__init__(*args, **kwargs)
            self.attributes = ProductAttributeHelper(self)

        def get_variations(self):
            if self.is_variant:
                variations =  _variation.models.Variation.objects.for_product(
                    self.product).filter(variant=self)
            else:
                variations =  _variation.models.Variation.objects.for_product(self)

            return variations.polymorphic_select_related('product')

        def save(self, *args, **kwargs):
            super(Product, self).save(*args, **kwargs)

            # Try to update variants
            # Product subtypes are not required
            # to have variants. Depends on wether or
            # not the product subtype was registered.
            downcasted = self.downcast()
            if (
                hasattr(downcasted, 'variants') and
                downcasted.variants.count() > 0
            ):
                for variant in downcasted.variants.all():
                    variant.save()

        class Meta(_product.models.Product.Meta):
            abstract = True

    _product.models.Product = Product
    _product.models.ProductQuerySet = ProductQuerySet


@load(before='finalize_attribute_Attribute')
def load_model():
    class AttributeQuerySet(_attribute.models.AttributeQuerySet):
        def for_product_or_variants_of(self, product):
            return (
                self.filter(
                    Q(values__product=product) | Q(
                        values__base_product=product
                    )
                ).distinct()
            )

        def which_variate_product(self, product):
            return self.filter(
                Q(variates=True) & (
                    Q(values__base_product=product) | Q(
                        values__product=product
                    ) & Q(values__variates=True)
                )
            ).distinct()

        def which_variate_variations(self, variations):
            # Query attribute/value combinations which occur less
            # times than the amount of variations. We can use this
            # to query variating attributes across the
            # given set of variations.
            attributes = _attribute.models.Attribute.objects.none()
            num_variations = variations.count()
            if num_variations > 1:
                values = (
                    _attribute.models.Value.objects.smart_values(
                        'attribute', 'value'
                    ).annotate(num=Count('attribute')).filter(
                        variations=variations,
                        num__lt=num_variations
                    ).order_by()
                )

                # Now query the attributes
                attributes = _attribute.models.Attribute.objects.filter(
                    pk__in=set([value['attribute'].pk for value in values])
                )

            return attributes

    class Attribute(_attribute.models.Attribute):

        variates = models.BooleanField(
            default=False,
            verbose_name=_("variates")
        )

        groups = models.BooleanField(default=False, verbose_name=_("groups"))

        def save(self, *args, **kwargs):
            old = None
            if self.pk:
                old = _attribute.models.Attribute.objects.get(pk=self.pk)
            super(Attribute, self).save(*args, **kwargs)
            if self.variates or old and old.variates:
                products = _product.models.Product.objects.filter(
                    product_q(
                        attribute=self,
                        through='base_product'
                    )
                )
                _variation.models.Variation.objects.invalidate(
                    products=products
                )

        class Meta(_attribute.models.Attribute.Meta):
            abstract = True

    _attribute.models.Attribute = Attribute
    _attribute.models.AttributeQuerySet = AttributeQuerySet


@load(before='finalize_attribute_Value')
def load_model():
    class ValueQuerySet(_attribute.models.ValueQuerySet):
        def for_product_or_variants_of(self, product):
            q = Q(product=product) | Q(base_product=product)
            return self.filter(q)

        def which_variate_product(self, product):
            return self.filter(
                Q(attribute__variates=True) & (
                    Q(base_product=product) | Q(
                        product=product
                    ) & Q(variates=True)
                )
            )

    class ValueManager(_attribute.models.ValueManager):
        def get_by_natural_key(
            self,
            attribute,
            product,
            value,
            variates,
            queryset=None
        ):

            queryset = self.filter(variates=variates)
            return super(ValueManager,
                         self).get_by_natural_key(attribute,
                                                  product,
                                                  value,
                                                  queryset=queryset)

    class Value(_attribute.models.Value):

        base_product = models.ForeignKey(
            'product.Product',
            db_index=True,
            null=True,
            blank=True,
            editable=False,
            related_name='variant_values'
        )

        variates = models.BooleanField(default=False, editable=False)

        def natural_key(self):
            return super(Value, self).natural_key() + (self.variates, )

        class Meta(_attribute.models.Value.Meta):
            abstract = True

    _attribute.models.Value = Value
    _attribute.models.ValueQuerySet = ValueQuerySet
    _attribute.models.ValueManager = ValueManager


@load(before='finalize_product_ProductRelatable')
def load_model():
    class ProductRelatable(_product.models.ProductRelatable):
        @classmethod
        def get_limit_choices_to(cls):
            return Q(
                content_type__in=ContentType.objects.get_for_models(
                    *_product.models.Product.SUBTYPES
                ).values()
            )

        def get_related_products(self):
            products = super(ProductRelatable, self).get_related_products()
            products = products.variants(exclude=True)
            return products

        class Meta(_product.models.ProductRelatable.Meta):
            abstract = True

    _product.models.ProductRelatable = ProductRelatable


@load(after='finalize_variation_Variation')
@load(before='finalize_product_ProductIndex')
def load_index():
    class ProductIndex(_product.indexes.ProductIndex):

        variation = indexing.ModelField(
            _variation.models.Variation,
            varieties=(lambda document: list(_variation.models.Variation.objects.for_product(document, allow_sync=False)) + [None])
        )

        def get_queryset(self):
            # We do not want to index and search variants
            queryset = super(ProductIndex, self).get_queryset()
            return queryset.variants(exclude=True)

        def get_attribute_value(self,
                                document,
                                attribute,
                                variation=None,
                                **variety):
            variation = variation or document
            value = variation.attributes[attribute.key]
            value = attribute.get_type().prep_index_value(value)
            return value

        def has_attribute(self,
                          document,
                          attribute,
                          variation=None,
                          **variety):
            variation = variation or document
            return attribute in variation.attributes

    _product.indexes.ProductIndex = ProductIndex
