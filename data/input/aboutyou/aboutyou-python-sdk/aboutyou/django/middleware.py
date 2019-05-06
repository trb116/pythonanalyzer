#-*- coding: utf-8 -*-
"""
:Author: Arne Simon [arne.simon@slice-dice.de]
"""
import django.core.exceptions

try:
    from django.conf import settings
    from django.contrib.auth import authenticate, login
except django.core.exceptions.ImproperlyConfigured:
    pass

import logging


logger = logging.getLogger("aboutyou.middleware")


class AboutyouMiddleware(object):
    """
    An authentication middleware which uses aboutyou access token.

    This class uses the access token in the Authorization header or
    the *aboutyou_access_token* cookie for authentication.

    .. rubric:: Usage

    Add the class in **settings.py** to the middleware classes.

    .. code-block:: python

        MIDDLEWARE_CLASSES = (
            ...
            'aboutyou.django.middleware.AboutyouMiddleware',
        )

        AUTH_REDIRECT_PATH = '/redirect'
    """
    def process_request(self, request):
        try:
            user = None

            if not request.user.is_authenticated():
                access_token = None

                # try to use the Authorization header
                if "HTTP_AUTHORIZATION" in request.META:
                    access_token = request.META["HTTP_AUTHORIZATION"].split(' ')[1]
                    logger.debug('got Authorization Header token: %s', access_token)
                else:
                    code = request.GET.get('code')
                    state = request.GET.get('state')

                    if code and state:
                        redirect_uri = request.build_absolut_uri(settings.AUTH_REDIRECT_PATH)

                        access_token = settings.AUTH.access_token(code, redirect_uri)['access_token']


                if access_token:
                    user = authenticate(access_token=access_token)

                    if user is not None and not user.is_anonymous():
                        login(request, user)
        except Exception:
            logger.exception('')
