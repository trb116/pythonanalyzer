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

from datetime import timedelta

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sellmo.core.loading import load
from sellmo.contrib.settings import settings_manager

import sellmo.apps.product as _product
import sellmo.contrib.availability as _availability
import sellmo.contrib.variation as _variation


_product.models['ProductPurchase'].inject(mixin_model(
    lambda: partials.ProductPurchase
))


_product.models['ProductManager'].inject(inherit_class(
    lambda: _availability.models.BaseAvailabilityManager,
    lambda: _availability.models.BaseBackorderManager
))


_product.models['ProductQuerySet'].inject(inherit_class(
    lambda: _availability.models.BaseAvailabilityQuerySet,
    lambda: _availability.models.BaseBackorderQuerySet
))


_product.models['Product'].inject(inherit_model(
    lambda: _availability.models.BaseAvailability,
    lambda: _availability.models.BaseBackorder
))


_variation.models['VariationManager'].inject(inherit_class(
    lambda: _availability.models.BaseAvailabilityManager
))


_variation.models['VariationQuerySet'].inject(inherit_class(
    lambda: _availability.models.BaseAvailabilityQuerySet
))


_variation.models['Variation'].inject(inherit_model(
    lambda: _availability.models.BaseAvailability
))
