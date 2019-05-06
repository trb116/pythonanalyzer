from sellmo.contrib.attribute.models import (Attribute, AttributeSet,
    AttributeChoice, Value)
from sellmo.contrib.attribute.admin import (
    BaseAttributeSetAdmin, AttributeSetParentListFilter)

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class AttributeChoiceAdmin(admin.TabularInline):

    model = AttributeChoice


class AttributeAdmin(admin.ModelAdmin):

    list_display = ['name', 'type', 'required', 'variates', 'key', 'indexed']
    list_filter = ['type', 'required', 'indexed', 'variates']

    search_fields = ['name', 'key']

    fieldsets = (
        (None, {
            'fields': ('name', 'type', 'key', 'required', 'sets')
        }),
        (_("Indexing"), {
            'fields': ('indexed',)
        }),
        (_("Variation"), {
            'fields': ('variates', 'groups',)
        }),
    )

    inlines = [AttributeChoiceAdmin]


class AttributeSetAdmin(BaseAttributeSetAdmin):

    list_display = ['full_name', 'name', 'parent']
    list_display_links = ['full_name', 'name']

    list_filter = [AttributeSetParentListFilter]
    search_fields = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'parent')
        }),
        (_("Display"), {
            'fields': ('sort_order',)
        }),
    )

    def full_name(self, instance):
        return instance.full_name
    full_name.short_description = _("full name")

    raw_id_fields = ['parent']


class ValueAdmin(admin.ModelAdmin):

    list_display = ['product', 'attribute', 'value']
    list_filter = ['attribute']

    search_fields = ['product__name']

    def value(self, obj):
        return obj.get_value()


admin.site.register(Attribute, AttributeAdmin)
admin.site.register(AttributeSet, AttributeSetAdmin)
admin.site.register(Value, ValueAdmin)
