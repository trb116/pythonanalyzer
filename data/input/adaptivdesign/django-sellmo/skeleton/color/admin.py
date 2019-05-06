from sellmo import modules

from django.contrib import admin


class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'value']


admin.site.register(modules.color.Color, ColorAdmin)
