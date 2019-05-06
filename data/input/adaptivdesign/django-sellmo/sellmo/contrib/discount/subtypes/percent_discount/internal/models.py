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

from decimal import Decimal

from sellmo.core.loading import load
from sellmo.apps.pricing import Price, StandardizedDecimalField

from django.db import models
from django.utils.translation import ugettext_lazy as _

import sellmo.contrib.discount as _discount
import sellmo.contrib.discount.subtypes.percent_discount as _percent_discount


@load(after='finalize_discount_Discount')
@load(action='finalize_discount_PercentDiscount')
def finalize_model():
    class PercentDiscount(
        _percent_discount.models.PercentDiscount, _discount.models.Discount
    ):

        rate = StandardizedDecimalField(
            default=Decimal('0.0'),
            verbose_name=_("rate"),
        )

        class Meta(
            _percent_discount.models.PercentDiscount.Meta,
            _discount.models.Discount.Meta
        ):
            app_label = 'discount'

    _percent_discount.models.PercentDiscount = PercentDiscount


class PercentDiscount(models.Model):
    def apply(self, price):

        # First we get the base amount
        # to apply the rate against.
        base_amount = price.amount

        # Now we can create the discount
        discount_amount = base_amount * self.rate
        discount = Price(
            discount_amount,
            currency=price.currency,
            component=self
        )

        # Apply discount
        price -= discount

        return price

    class Meta:
        abstract = True
        verbose_name = _("percent discount")
        verbose_name_plural = _("percent discounts")
