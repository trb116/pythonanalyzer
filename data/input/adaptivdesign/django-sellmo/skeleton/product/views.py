from sellmo import modules
from sellmo.core.decorators import link

from django.shortcuts import render


namespace = modules.product.namespace


@chaining.link
def product(request, product, context, **kwargs):
    context.update({
        'product': product,
        'category': product.primary_category
    })
    return render(request, 'product/product.html', context)
