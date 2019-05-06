from django.contrib import admin

from sellmo.contrib.variation.models import Variation


class VariationAdmin(admin.ModelAdmin):
    search_fields = ['description']
    list_display = ['description', 'stock']
    list_editable = ['stock']

    def has_add_permission(self, request):
        return False


admin.site.register(Variation, VariationAdmin)
