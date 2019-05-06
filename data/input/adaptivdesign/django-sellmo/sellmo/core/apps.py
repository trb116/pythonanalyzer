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

import logging
from collections import OrderedDict
from importlib import import_module

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string, module_has_submodule
from django.utils import six

from sellmo.utils.sorting import topological_sort

from .loading.loader import loader
from .signals import (
    pre_init, post_init, pre_load, post_load, pre_inject, post_inject,
    pre_configure, post_configure, pre_link, post_link
)

logger = logging.getLogger('sellmo')

sellmo_apps = OrderedDict()


class SellmoAppConfigMeta(type):
    def __new__(cls, name, bases, attrs):
        out = super(SellmoAppConfigMeta, cls).__new__(cls, name, bases, attrs)

        # __new__ will also be called for base classes.
        # Do not proceed with any further initialization. Ignore it..
        if out.__ignore__:
            out.__ignore__ = False
            return out

        # Generate auto label
        if not 'label' in attrs:
            out.label = '_'.join(out.name.split('.'))

        return out


class SellmoAppConfig(six.with_metaclass(SellmoAppConfigMeta, AppConfig)):

    __ignore__ = True

    dependencies = []

    def __init__(self, *args, **kwargs):
        super(SellmoAppConfig, self).__init__(*args, **kwargs)
        sellmo_apps[self.name] = self

    def load_module(self, module_name):
        if module_has_submodule(self.module, module_name):
            models_module_name = '{0}.{1}'.format(self.name, module_name)
            self.models_module = import_module(models_module_name)


class DefaultConfig(AppConfig):

    name = 'sellmo'
    setup_modules = ['sellmo.caching', 'sellmo.celery']

    def __init__(self, *args, **kwargs):
        super(DefaultConfig, self).__init__(*args, **kwargs)

        self.apps = None

        pre_init.send(self)

        for name in self.setup_modules:
            module = import_module(name)
            if module.enabled:
                module.setup(self)

    def load_apps_module(self, module):
        for app in self.apps:
            logger.debug("Importing module %s for app %s" % (module, app))
            app.load_module(module)

    def ready(self):

        dependencies = OrderedDict()
        all_apps = list(six.itervalues(sellmo_apps))
        for app in all_apps:
            app_dependencies = set()

            # Explicit dependencies
            for dependency in app.dependencies:
                if dependency not in sellmo_apps:
                    raise ImproperlyConfigured(
                        "Missing app %s required "
                        "by %s" % (dependency, app.name)
                    )
                app_dependencies.add(sellmo_apps[dependency])

            dependencies[app] = app_dependencies

        self.apps = list(topological_sort(dependencies))

        # Modules are first imported followed lastly by
        # extra imports. Module order first, then app order for each
        # module.

        # Delayed loading registration is now done. We can now call all
        # delayed functions in correct order.

        pre_inject.send(self)
        self.load_apps_module('inject')
        post_inject.send(self)

        pre_load.send(self)
        loader.load()
        post_load.send(self)

        pre_configure.send(self)
        self.load_apps_module('configure')
        post_configure.send(self)

        pre_link.send(self)
        self.load_apps_module('links')
        post_link.send(self)

        # We are done
        post_init.send(self)
