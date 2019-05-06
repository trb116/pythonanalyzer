from extras.navigation.models import NavigationItem, NavigationArgument
from extras.navigation.registration import registry

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class NavigationArgumentInline(admin.TabularInline):

    model = NavigationArgument

    # Grappelli only
    related_lookup_fields = {
        'generic': [['argument_content_type', 'argument_object_id']],
    }

    autocomplete_lookup_fields = {
        'generic': [['argument_content_type', 'argument_object_id']],
    }


class NavigationItemAdmin(admin.ModelAdmin):

    inlines = [NavigationArgumentInline]

    list_display = ['full_title', 'active', 'placement', 'reversed_url']
    list_display_links = ['full_title']

    list_filter = ['active', 'placement']
    search_fields = ['title']

    raw_id_fields = ['parent']

    # Grappelli only
    autocomplete_lookup_fields = {
        'fk': ['parent'],
    }

    fieldsets = (
        (None, {
            'fields': ('title', 'parent', 'view')
        }),
        (_("Display"), {
            'fields': ('placement', 'active', 'sort_order')
        }),
    )

    def reversed_url(self, obj):
        reversed_url = obj.reversed_url
        if reversed_url:
            return u'<a href="%s">%s</a>' % (reversed_url, reversed_url)
        else:
            return None
    reversed_url.allow_tags = True

    def get_queryset(self, request):
        return super(NavigationItemAdmin, self).get_queryset(request).flat_ordered()


admin.site.register(NavigationItem, NavigationItemAdmin)
