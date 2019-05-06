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
from sellmo.core.indexing import indexer
from sellmo.core.http.query import QueryString
from sellmo.apps.customer.models import CustomerGroup

from .models import Product # NOQA


class BaseProductSet(object):

    @classmethod
    @chaining.define(binds=True, takes_result=True)
    def from_request(cls, products, request, query=None, **kwargs):
        if query is None:
            query = QueryString(request)
            yield chaining.update(query=query)

        if products is None:
            products = indexer.get_index('product')
            products = products.search(get_product_queryset())

        # Retrieve price from index
        if products.can_use_price_field('price'):
            products = products.with_price_field('price')

        # Handle price sorting
        if query and products.can_use_price_field('price'):
            if ('sort', 'price') in query:
                products = products.order_by_price('price')
            elif ('sort', '-price') in query:
                products = products.order_by_price('-price')

        # Filter on customer group
        if products.can_use_field('customer_group'):
            customer_group = CustomerGroup.get_current()
            products = products.filter(customer_group=customer_group)

        yield products
        products = (yield chaining.forward).result

        if not products.bare_is_set():
            # Ideally we want to fetch final prices
            products = products.set_bare(False)
            yield products

    from_request.reserved_url_params = []

    def get_filters(filters, facets, **kwargs):
        if filters is None:
            filters = []
            yield filters

    def product_queryset(self):
        return Product.objects.all().polymorphic()
