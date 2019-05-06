from sellmo import modules

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


class PurchaseInline(admin.TabularInline):
    model = modules.purchase.Purchase
    extra = 0


class CartAdmin(admin.ModelAdmin):

    inlines = [PurchaseInline]
    list_display = ['id', 'total_amount', 'modified']


admin.site.register(modules.cart.Cart, CartAdmin)
