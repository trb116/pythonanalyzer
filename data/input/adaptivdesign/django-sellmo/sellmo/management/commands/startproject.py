# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os.path
from importlib import import_module

from optparse import make_option

from django.core.management.base import CommandError
from django.utils.crypto import get_random_string

from sellmo.management.template import TemplateCommand

DEFAULT_APPS = [
    'store', 'purchase', 'product', 'pricing', 'category', 'attribute',
    'variation', 'cart', 'checkout', 'account', 'settings', 'mailing',
    'customer', 'shipping', 'payment', 'tax', 'discount', 'availability',
    'search', 'brand', 'color'
]


def handle_apps(apps):
    """
    Organizes multiple apps that are separated with commas or passed by
    using --apps/-a multiple times.
    For example: running 'sellmo-cli startproject -a store,product -a cart'
    would result in an app list: ['store', 'product', 'cart']
    >>> store(['store', 'store,product'', 'cart])
    {'store', 'product, 'cart}
    """
    app_list = []
    for app in apps:
        app_list.extend(app.replace(' ', '').split(','))
    return set(app_list)


class Command(TemplateCommand):
    help = (
        "Creates a Django Sellmo project directory structure for the given "
        "project name in the current directory or optionally in the "
        "given directory."
    )

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--apps',
            '-a',
            dest='apps',
            action='append',
            default=DEFAULT_APPS,
            help='Sellmo apps to create (default: "{default}"). '
            'Separate multiple apps with commas, or use '
            '-a multiple times.'.format(default=','.join(DEFAULT_APPS))
        )
        parser.add_argument(
            '--celery',
            dest='celery',
            action='store_true',
            default=False
        )

    def handle(self, name, target=None, *args, **options):

        self.validate_name(name, "project")

        # Check that the project_name cannot be imported.
        try:
            import_module(name)
        except ImportError:
            pass
        else:
            raise CommandError(
                "%r conflicts with the name of an existing "
                "Python module and cannot be used as a "
                "project name. Please try another name." % name
            )

        # Create a random SECRET_KEY hash to put it in the main settings.
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        options['secret_key'] = get_random_string(50, chars)

        # Collect sellmo apps
        apps = tuple(handle_apps(options.pop('apps')))

        super(Command, self).handle(
            'project',
            name,
            target,
            apps=apps,
            **options
        )
        self.stdout.write(
            "\nNow head to %s and run required commands:" %
            os.path.abspath(name)
        )
        self.stdout.write(
            "\n\nInstall additional requirements for your project:\npip install -r requirements.txt"
        )
        self.stdout.write(
            "\n\nCreate initial migrations:\npython manage.py makemigrations %s"
            % ' '.join(apps)
        )
        self.stdout.write("\n\nCreate database:\npython manage.py migrate")
        self.stdout.write(
            "\n\nCreate superuser:\npython manage.py createsuperuser <yourname>"
        )

        self.stdout.write(
            "\n\nTo serve and compile staticfiles head to %s:" %
            os.path.abspath(os.path.join(name, name, 'static'))
        )
        self.stdout.write("\n\nInstall node packages:\nnpm install")
        self.stdout.write("\n\nInstall bower packages:\nbower install")
        self.stdout.write("\n\nServe development staticfiles: gulp serve")

    def preprocess_file(self, filename, context):
        # First make sure this app should be generated
        app = context.get('app', None)
        if app is not None and app not in context.get('apps'):
            return False
