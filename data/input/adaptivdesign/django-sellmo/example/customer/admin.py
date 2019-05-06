from django import forms
from django.contrib import admin

from sellmo.apps.customer.models import Customer, CustomerGroup, Address


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


class CustomerAdmin(admin.ModelAdmin):

    list_display = ['first_name', 'last_name']
    inlines = [AddressInline]
    raw_id_fields = ['user']


class CustomerGroupAdmin(admin.ModelAdmin):

    list_display = ['name']


admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerGroup, CustomerGroupAdmin)
