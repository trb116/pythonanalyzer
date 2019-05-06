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

import sellmo.contrib.shipping as _shipping
import sellmo.contrib.shipping.methods.flat_shipping as _flat_shipping


@load(after='finalize_shipping_ShippingMethod')
@load(action='finalize_shipping_FlatShippingMethod')
def finalize_model():
    class FlatShippingMethod(
        _flat_shipping.models.FlatShippingMethod,
        _shipping.models.ShippingMethod
    ):
        class Meta(
            _flat_shipping.models.FlatShippingMethod.Meta,
            _shipping.models.ShippingMethod.Meta
        ):

            app_label = 'shipping'

    _flat_shipping.models.FlatShippingMethod = FlatShippingMethod


class FlatShippingMethod(models.Model):

    costs = PriceField(
        default=0,
        multi_currency=True,
        components=None,
        verbose_name=_("shipping rate")
    )

    def get_method(self, carrier=None):

        from .method import FlatShippingMethod

        return FlatShippingMethod(
            identifier,
            name,
            self.costs,
            carrier=carrier
        )

    class Meta:
        abstract = True
        verbose_name = _("flat shipping method")
        verbose_name_plural = _("flat shipping methods")
