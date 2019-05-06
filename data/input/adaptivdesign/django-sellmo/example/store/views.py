from sellmo.core.http.query import QueryString
from sellmo.apps.product.routines import list_products_from_request

from django.template.response import TemplateResponse

def index(request):
    query = QueryString(request)

    # Lets query featured products for our store index
    products = list_products_from_request(request, featured=True, query=query)
    context = {
        'products': products[:8], 'q': query
    }

    return TemplateResponse(request, 'store/index.html', context)
