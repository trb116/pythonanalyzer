from django.contrib import admin

from sellmo import modules
from sellmo.contrib.settings.admin import SettingsAdminBase


class SettingsAdmin(SettingsAdminBase):
    pass


admin.site.register(modules.settings.SiteSettings, SettingsAdmin)
