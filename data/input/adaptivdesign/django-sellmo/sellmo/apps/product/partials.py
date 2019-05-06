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
from django.utils.translation import ugettext_lazy as _

from sellmo.apps.purchase.exceptions import PurchaseInvalid

import sellmo.apps.product as _product
import sellmo.apps.purchase as _purchase
import sellmo.apps.cart as _cart


class AddProductToCartForm(forms.Form):
    
    def get_purchase_args(self):
        args = super(AddProductToCartForm, self).get_purchase_args()
        slug = self.cleaned_data['product']
        try:
            product = _product.models.Product.objects.polymorphic().get(
                slug=slug)
        except _product.models.Product.DoesNotExist:
            raise PurchaseInvalid()

        args.update({'product': product})

        return args


class AddToCartForm(forms.Form):

    @classmethod
    def factory(cls, data=None, product=None, **kwargs):
        Form = super(AddToCartForm, cls).factory(
            data=data,
            product=product,
            **kwargs
        )

        if data is not None and 'product' in data:
            try:
                product = _product.models.Product.objects.polymorphic().get(
                    slug=data['product'])
            except _product.models.Product.DoesNotExist:
                raise PurchaseInvalid(_("Product is no longer available."))

        if product is not None:

            Form = type('AddToCartForm', (AddProductToCartForm, Form), {
                'product': forms.CharField(
                    initial=product.slug,
                    widget=forms.HiddenInput
                )
            })

        return Form


class Purchase(models.Model):

    @classmethod
    def factory(cls, product=None, **kwargs):
        if product is not None:
            return _product.models.ProductPurchase
        return super(Purchase, cls).factory(product=product, **kwargs)

    class Meta:
        abstract = True


class PurchaseQuerySet(models.QuerySet):

    def mergeable_with(self, purchase):
        purchase = purchase.downcast()
        queryset = self

        # We could simply import .models.ProductPurchase here, but
        # why would we if it affects performance every time this
        # method is called.
        if isinstance(purchase, _product.models.ProductPurchase):
            queryset = queryset.filter(
                productpurchase__product=purchase.product
            )

        return super(PurchaseQuerySet, queryset).mergeable_with(purchase)
