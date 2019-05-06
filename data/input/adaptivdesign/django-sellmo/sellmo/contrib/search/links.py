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

import operator

from sellmo.core import chaining
from sellmo.core.indexing import SQ
from sellmo.apps.product.routines import list_products_from_request

from .constants import SEARCH_URL_PARAM, SEARCH_FIELDS


@chaining.link(list_products_from_request, takes_result=True)
def _list_products_from_request(products, request, query=None, **kwargs):
    
    def construct_search(field):
        if field.startswith('^'):
            return "%s__startswith" % field[1:]
        elif field.startswith('='):
            return "%s__exact" % field[1:]
        else:
            return "%s__contains" % field

    if SEARCH_URL_PARAM in query:

        term = ' '.join(query[SEARCH_URL_PARAM])
        supported_search_fields = []

        # Find out which fields are supported
        for field in SEARCH_FIELDS:

            if field.startswith('^'):
                field = field[1:]
            elif field.startswith('='):
                field_name = field[1:]
            else:
                field_name = field

            if products.can_use_field(field_name):
                supported_search_fields.append(field)

        if supported_search_fields and term:
            orm_lookups = [
                construct_search(str(field))
                for field in supported_search_fields
            ]
            for bit in term.split():
                or_queries = [
                    SQ(**{orm_lookup: bit}) for orm_lookup in orm_lookups
                ]
                products = products.filter(reduce(operator.or_, or_queries))

        yield products
