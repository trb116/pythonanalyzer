from sellmo import modules

from django.contrib import admin


class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(modules.brand.Brand, BrandAdmin)
