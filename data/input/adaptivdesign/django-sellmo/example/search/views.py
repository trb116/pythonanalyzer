from sellmo.core.http.query import QueryString
from sellmo.apps.product.routines import (list_products_from_request,
    product_filters_from_request)
from sellmo.contrib.search.constants import SEARCH_URL_PARAM

from product.utils import paginate

from django.template.response import TemplateResponse


def search(request, context=None, **kwargs):
    if context is None:
        context = {}

    query = QueryString(request)
    context.update({
        'q': query
    })

    if SEARCH_URL_PARAM in query and query[SEARCH_URL_PARAM]:
        products = list_products_from_request(request, query=query)
        products = paginate(request, products)
        product_filters = product_filters_from_request(request, products.object_list.facets(), query=query)

        context.update({
            'products': products,
            'product_filters': product_filters,

        })

    return TemplateResponse(request, 'search/search.html', context)
