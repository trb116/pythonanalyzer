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
from sellmo.apps.pricing import PriceField

from django.db import models
from django.utils.translation import ugettext_lazy as _

import sellmo.contrib.product.pricing.qty_pricing as _qty_pricing


@load(action='finalize_product_ProductQtyPrice')
def finalize_model():
    class ProductQtyPrice(_qty_pricing.models.ProductQtyPrice):

        objects = (
            _qty_pricing.models.ProductQtyPriceManager.from_queryset(
                _qty_pricing.models.ProductQtyPriceQuerySet
            )
        )()

        class Meta(_qty_pricing.models.ProductQtyPrice.Meta):
            app_label = 'product'

    _qty_pricing.models.ProductQtyPrice = ProductQtyPrice


class ProductQtyPriceQuerySet(models.QuerySet):
    def for_qty(self, qty):
        match = self.filter(qty__lte=qty).order_by('-qty').first()
        if match:
            return match
        raise self.model.DoesNotExist()


class ProductQtyPriceManager(models.Manager):
    pass


class ProductQtyPrice(models.Model):

    qty = models.PositiveIntegerField(verbose_name=_("quantity"), default=1)

    amount = PriceField(
        multi_currency=True,
        components=None,
        verbose_name=_("amount")
    )

    product = models.ForeignKey(
        'product.Product',
        related_name='qty_prices',
        editable=False
    )

    def __unicode__(self):
        return unicode(_("{0} qty or more").format(self.qty))

    class Meta:
        abstract = True
        ordering = ['qty']
        verbose_name = _("qty price")
        verbose_name_plural = _("qty prices")
