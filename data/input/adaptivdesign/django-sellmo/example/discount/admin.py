from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin

from sellmo.contrib.discount.models import Discount
from sellmo.contrib.discount.subtypes.percent_discount.models import PercentDiscount
from sellmo.contrib.discount.subtypes.fixed_discount.models import FixedDiscount


class DiscountChildAdmin(PolymorphicChildModelAdmin):
    base_model = Discount
    filter_horizontal = ['products', 'categories']


class DiscountParentAdmin(PolymorphicParentModelAdmin):
    base_model = Discount
    child_models = []

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']

    def get_queryset(self, queryset):
        return Discount.objects.all()


admin.site.register(Discount, DiscountParentAdmin)


# Percent discount

class PercentDiscountAdmin(DiscountChildAdmin):
    pass


DiscountParentAdmin.child_models += [(PercentDiscount, PercentDiscountAdmin)]


# Fixed discount

class FixedDiscountAdmin(DiscountChildAdmin):
    pass


DiscountParentAdmin.child_models += [(FixedDiscount, FixedDiscountAdmin)]
