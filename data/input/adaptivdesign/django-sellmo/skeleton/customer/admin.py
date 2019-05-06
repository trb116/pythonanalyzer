from django import forms
from django.contrib import admin

from sellmo import modules

from extras.admin.reverse import ReverseModelAdmin


class AddressForm(forms.ModelForm):
    pass


class CustomerAdmin(ReverseModelAdmin):
    inline_type = 'stacked'
    inline_reverse = [('{0}_address'.format(address), {'form': AddressForm})
                      for address in modules.customer.address_types]

    list_display = ['first_name', 'last_name']

    if modules.customer.auth_enabled:
        raw_id_fields = ['user']


class CustomerGroupAdmin(admin.ModelAdmin):

    list_display = ['name']


admin.site.register(modules.customer.Customer, CustomerAdmin)
admin.site.register(modules.customer.CustomerGroup, CustomerGroupAdmin)
