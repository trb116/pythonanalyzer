from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin

from sellmo.contrib.tax.models import Tax, TaxRule, ProductTaxClass
from sellmo.contrib.tax.subtypes.percent_tax.models import PercentTax
from sellmo.contrib.tax.subtypes.flat_tax.models import FlatTax

class TaxChildAdmin(PolymorphicChildModelAdmin):
    base_model = Tax


class TaxParentAdmin(PolymorphicParentModelAdmin):
    base_model = Tax
    child_models = []

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']

    def get_queryset(self, queryset):
        return modules.tax.Tax.objects.all()


class TaxRuleAdmin(admin.ModelAdmin):
    pass


class ProductTaxClassAdmin(admin.ModelAdmin):
    pass


admin.site.register(Tax, TaxParentAdmin)
admin.site.register(TaxRule, TaxRuleAdmin)
admin.site.register(ProductTaxClass, ProductTaxClassAdmin)


# Percent tax

class PercentTaxAdmin(TaxChildAdmin):
    pass


TaxParentAdmin.child_models += [(PercentTax, PercentTaxAdmin)]


# Flat tax

class FlatTaxAdmin(TaxChildAdmin):
    pass


TaxParentAdmin.child_models += [(FlatTax, FlatTaxAdmin)]
