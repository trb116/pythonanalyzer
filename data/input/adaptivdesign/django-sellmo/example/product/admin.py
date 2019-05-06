from sellmo.apps.product.models import Product
from sellmo.apps.pricing.helpers import price_field_names
from sellmo.contrib.category.admin import (ProductCategoryListFilter,
    ProductCategoriesMixin)
from sellmo.contrib.variation.admin import (VariantAttributeMixin,
    ProductVariationMixin)
from sellmo.contrib.attribute.admin import ProductAttributeMixin
from sellmo.contrib.tax.admin import ProductTaxClassesMixin
from sellmo.contrib.discount.admin import ProductDiscountsMixin
from sellmo.contrib.product.pricing.qty_pricing.models import ProductQtyPrice
from sellmo.contrib.product.subtypes.simple_product.models import SimpleProduct
from sellmo.contrib.product.subtypes.configurable_product.models import ConfigurableProduct
from sellmo.contrib.variation.models import (SimpleProductVariant,
    ConfigurableProductVariant)

from django.contrib import admin
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail import get_thumbnail

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin

import logging
logger = logging.getLogger(__name__)


class ProductQtyPriceInline(admin.TabularInline):
    model = ProductQtyPrice


class ProductChildAdmin(
        ProductTaxClassesMixin,
        ProductDiscountsMixin,
        ProductCategoriesMixin,
        ProductAttributeMixin,
        ProductVariationMixin,
        PolymorphicChildModelAdmin):

    base_model = Product
    inlines = [ProductQtyPriceInline]
    fieldsets = (
        (_("Product"), {
            'fields': ('name', 'sku', 'main_image', 'short_description', 'attribute_set')
        }),
        (_("Product pricing"), {
            'fields': (tuple(price_field_names('fixed_price', multi_currency=True, components=None)), 'tax_classes', 'discounts')
        }),
        (_("Product availability"), {
            'fields': ('allow_backorders', 'supplier', 'min_backorder_time', 'max_backorder_time', 'stock',)
        }),
        (_("Store arrangement"), {
            'fields': ('slug', 'categories', 'primary_category', 'active', 'featured',)
        }),
    )

    filter_horizontal = ['categories']

    prepopulated_fields = {
        'slug' : ('name',),
    }

    raw_id_fields = ['primary_category']
    autocomplete_lookup_fields = {
        'fk': ['primary_category'],
    }


class VariantInline(VariantAttributeMixin, admin.StackedInline):

    fieldsets = (
        (_("Product information"), {
            'fields': ('name', 'sku', 'main_image', 'short_description',)
        }),
        (_("Store arrangement"), {
            'fields': ('slug',)
        }),
        (_("Product pricing"), {
            'fields': (tuple(price_field_names('price_adjustment', multi_currency=True, components=None)),)
        }),
    )


class ProductParentAdmin(PolymorphicParentModelAdmin):

    base_model = Product
    polymorphic_list = False
    list_display = ['slug']
    list_display_links = ['slug']
    search_fields = ['slug']

    child_models = []


    list_display = ['thumbnail', 'name', 'active', 'featured', 'slug', 'sku', 'stock', 'primary_category']
    list_display_links = ['name', 'slug']
    list_editable = ['active', 'featured']

    list_filter = [ProductCategoryListFilter, 'active', 'featured']
    search_fields = ['name', 'slug', 'sku']

    def get_queryset(self, queryset):
        return Product.objects.variants(exclude=True)

    def thumbnail(self, instance):
        if instance.main_image:
            try:
                thumbnail = get_thumbnail(instance.main_image, '30x30', crop='center', quality=100)
                return '<img src="%s"/>' % (thumbnail.url)
            except IOError as ex:
                logger.warning(ex)
        return ''

    thumbnail.allow_tags = True
    thumbnail.short_description = _("thumbnail")


admin.site.register(Product, ProductParentAdmin)


# Simple product

class SimpleVariantInline(VariantInline):
    model = SimpleProductVariant
    fk_name = 'product'


class SimpleProductAdmin(ProductChildAdmin):
    inlines = ProductChildAdmin.inlines + [SimpleVariantInline]


class ConfigurableVariantInline(VariantInline):
    model = ConfigurableProductVariant
    fk_name = 'product'


class ConfigurableProductAdmin(ProductChildAdmin):
    inlines = ProductChildAdmin.inlines + [ConfigurableVariantInline]


ProductParentAdmin.child_models += [
    (SimpleProduct, SimpleProductAdmin),
    (ConfigurableProduct, ConfigurableProductAdmin)]
