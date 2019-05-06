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
from sellmo.apps.pricing import Price
from sellmo.apps.product.routines import list_products_from_request

from .constants import INDEXABLE_QTYS
from .models import ProductQtyPrice


@chaining.link(list_products_from_request, takes_result=True, provides=['qty'])
def _list_products_from_request(products, request, qty=None, **kwargs):
    if qty is None:
        qty = INDEXABLE_QTYS[-1]
        yield chaining.update(qty=qty)

    if products.can_use_field('qty'):
        products = products.filter(qty=qty)
        yield products


@chaining.link(Price.calculate, takes_result=True)
def _calculate(price, product=None, qty=1, **kwargs):
    if price is None and not (product is None or qty is None):
        try:
            qty_price = ProductQtyPrice.objects.filter(
                product=product).for_qty(qty)
        except ProductQtyPrice.DoesNotExist:
            pass
        else:
            price = qty_price.amount
            yield price
