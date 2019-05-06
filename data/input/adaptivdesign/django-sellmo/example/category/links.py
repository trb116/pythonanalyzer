from sellmo.core import chaining
from sellmo.core.http.query import QueryString
from sellmo.apps.product.routines import (list_products_from_request,
    product_filters_from_request)
from sellmo.contrib.category.views import category

from django.shortcuts import render
from django.template.response import TemplateResponse

from product.utils import paginate


@chaining.link(category)
def _category(request, category, **kwargs):
    query = QueryString(request)

    # Pass queryset through product module and include http query
    # for further filtering and sorting
    products = list_products_from_request(request, category=category, query=query)

    # Get root category
    if not category.is_leaf_node():
        root = category
    elif category.is_child_node():
        root = category.parent
    else:
        root = category

    products = paginate(request, products)
    product_filters = product_filters_from_request(request, products.object_list.facets(), category=category, query=query)
    
    yield TemplateResponse(request, 'category/category.html', {
        'products': products,
        'product_filters': product_filters,
        'root': root,
        'category': category,
        'q': query
    })
