from sellmo import modules

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class SupplierAdmin(admin.ModelAdmin):

    list_display = ['name', 'allow_backorders']
    fields = ['name', 'allow_backorders', 'min_backorder_time', 'max_backorder_time']


admin.site.register(modules.availability.Supplier, SupplierAdmin)
