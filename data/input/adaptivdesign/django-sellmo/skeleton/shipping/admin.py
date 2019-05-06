from sellmo import modules

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


class ShippingMethodChildAdmin(PolymorphicChildModelAdmin):
    pass


class ShippingMethodParentAdmin(PolymorphicParentModelAdmin):
    base_model = modules.shipping.ShippingMethod
    child_models = []

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


class ShippingCarrierAdmin(admin.ModelAdmin):
    pass


admin.site.register(modules.shipping.ShippingMethod, ShippingMethodParentAdmin)
admin.site.register(modules.shipping.ShippingCarrier, ShippingCarrierAdmin)


# Flat shipping

class FlatShippingMethodAdmin(ShippingMethodChildAdmin):
    base_model = modules.shipping.ShippingMethod


ShippingMethodParentAdmin.child_models += [
    (modules.shipping.FlatShippingMethod, FlatShippingMethodAdmin)]


# Tiered shipping


class TieredShippingTierInline(admin.TabularInline):
    model = modules.shipping.TieredShippingTier


class TieredShippingMethodAdmin(ShippingMethodChildAdmin):
    base_model = modules.shipping.ShippingMethod
    inlines = ShippingMethodChildAdmin.inlines + [TieredShippingTierInline]


ShippingMethodParentAdmin.child_models += [
    (modules.shipping.TieredShippingMethod, TieredShippingMethodAdmin)]
