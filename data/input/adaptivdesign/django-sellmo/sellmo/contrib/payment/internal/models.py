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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo.core.loading import load
from sellmo.apps.pricing import PriceField

import polymorphism

import sellmo.contrib.payment as _payment


@load(action='finalize_payment_Payment')
def finalize_model():
    class Payment(_payment.models.Payment):

        objects = _payment.models.PaymentManager.from_queryset(
            _payment.models.PaymentQuerySet)()

        class Meta(_payment.models.Payment.Meta):
            app_label = 'payment'

    _payment.models.Payment = Payment


class PaymentQuerySet(polymorphism.PolymorphicQuerySet):
    pass


class PaymentManager(polymorphism.PolymorphicManager):
    pass


class Payment(polymorphism.PolymorphicModel):

    instant = True

    order = polymorphism.PolymorphicOneToOneField(
        'checkout.Order',
        null=True,
        related_name='order_payment',
        polymorphic_related=True,
        editable=False
    )

    method_string = models.CharField(max_length=40, editable=False)

    description = models.CharField(
        max_length=255,
        verbose_name=_("description")
    )

    costs = PriceField(default=0, verbose_name=_("costs"))

    def resolve_method(self):
        # If a payment is subclassed it can resolve a method if desired.
        # Return None if method no longer is applicable.
        return NotImplemented

    def __unicode__(self):
        return self.description

    class Meta:
        abstract = True
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
