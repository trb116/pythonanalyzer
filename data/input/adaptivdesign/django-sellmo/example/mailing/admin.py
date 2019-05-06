from django.contrib import admin

from sellmo.contrib.mailing.models import MailMessage

class MailMessageAdmin(admin.ModelAdmin):

    list_display = ['delivered', 'message_type', 'send',
                    'send_to', 'message_reference', 'failure_message']
    list_display_links = ['message_reference']


admin.site.register(MailMessage, MailMessageAdmin)
