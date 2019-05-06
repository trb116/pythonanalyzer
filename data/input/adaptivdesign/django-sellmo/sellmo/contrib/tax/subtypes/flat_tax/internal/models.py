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
from sellmo.contrib.settings import settings_manager

from django.db import models
from django.utils.translation import ugettext_lazy as _

import sellmo.contrib.tax as _tax
import sellmo.contrib.tax.subtypes.flat_tax as _flat_tax


@load(after='finalize_tax_Tax')
@load(action='finalize_tax_FlatTax')
def finalize_model():
    class FlatTax(_flat_tax.models.FlatTax, _tax.models.Tax):
        class Meta(_flat_tax.models.FlatTax.Meta, _tax.models.Tax.Meta):
            app_label = 'tax'

    _flat_tax.models.FlatTax = FlatTax


class FlatTax(models.Model):

    amount = StandardizedDecimalField(
        default=Decimal('0.0'),
        verbose_name=_("amount"),
    )

    def apply(self, price):

        tax_inclusive = settings_manager['tax_inclusive']

        # Now we can create the tax
        tax_amount = self.amount
        tax = Price(tax_amount, currency=price.currency, component=self)

        # Apply tax
        price += tax

        # Handle tax inclusive
        if tax_inclusive:
            price -= Price(tax_amount, currency=price.currency)

        return price

    class Meta:
        abstract = True
        verbose_name = _("flat tax")
        verbose_name_plural = _("flat taxes")
