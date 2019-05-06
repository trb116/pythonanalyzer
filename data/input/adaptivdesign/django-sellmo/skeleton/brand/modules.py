from sellmo import modules, Module
from sellmo.core.decorators import context_processor
from sellmo.core import chaining

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from brand.models import (
    Brand,
    BrandManager,
    BrandQuerySet
)


class BrandModule(Module):

    namespace = 'brand'
    Brand = Brand
    BrandManager = BrandManager
    BrandQuerySet = BrandQuerySet

    @context_processor
    @chaining.define
    def brands_context(self, request, context=None, **kwargs):
        context = context or {}
        if 'brands' not in context:
            context['brands'] = modules.brand.Brand.objects.all()
        yield context
