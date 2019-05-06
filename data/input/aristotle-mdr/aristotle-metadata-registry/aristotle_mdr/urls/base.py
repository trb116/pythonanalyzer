import notifications.urls
import autocomplete_light
# import every app/autocomplete_light_registry.py

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.views import password_reset
from django.contrib import admin
from django.views.generic.base import RedirectView
from aristotle_mdr.views.user_pages import friendly_redirect_login

autocomplete_light.autodiscover()
admin.autodiscover()

urlpatterns = [
    url(r'^login/?$', friendly_redirect_login, name='friendly_login'),
    url(r'^logout/?$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^ckeditor/', include('aristotle_mdr.urls.ckeditor_uploader')),
    url(r'^account/notifications/', include(notifications.urls, namespace="notifications")),
    url(r'^account/password/reset/$', password_reset),  # , {'template_name': 'my_templates/password_reset.html'}
    url(r'^account/password/reset_done/$', password_reset),  # , {'template_name': 'my_templates/password_reset.html'}
    url(
        r'^user/password/reset/$',
        'django.contrib.auth.views.password_reset',
        {'post_reset_redirect': '/user/password/reset/done/'},
        name="password_reset"
    ),
    url(
        r'^user/password/reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        name="password_reset_done"
    ),
    url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'post_reset_redirect': '/user/password/done/'}),
    url(r'^user/password/done/$',
        'django.contrib.auth.views.password_reset_complete'),

    url(r'^account/password/?$', RedirectView.as_view(url='account/home/', permanent=True)),
    url(r'^account/password/change/?$', 'django.contrib.auth.views.password_change', name='password_change'),
    url(r'^account/password/change/done/?$', 'django.contrib.auth.views.password_change_done', name='password_change_done'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
