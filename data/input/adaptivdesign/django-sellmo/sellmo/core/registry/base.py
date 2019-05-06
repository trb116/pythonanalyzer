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

import sys
import traceback
from types import ModuleType
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.utils import six
from django.utils.functional import cached_property

from .exceptions import RegistryError

allowed = None


def should_fix_type(typ):
    global allowed
    if allowed is None:
        allowed = ['sellmo']
        for app in apps.get_app_configs():
            allowed.append(app.name)
    return any(typ.__module__.startswith(name) for name in allowed)



class ModuleAttribute(object):

    def __init__(self, module_name, name):
        self.module_name = module_name
        self.name = name
        self._accessed = False
        self._access_traceback = None
        self._injection_handlers = []

    def inject(self, handler):
        self._injection_handlers.insert(0, handler)

    @property
    def is_accesed(self):
        return self._accessed

    @property
    def is_assigned(self):
        return hasattr(self, '_value')

    def access(self):
        if not self._accessed:
            if getattr(settings, 'DEBUG', False):
                self._access_traceback = traceback.extract_stack()
            value = self._value
            for handler in self._injection_handlers:
                try:
                    value = handler(value)
                except Exception as ex:
                    raise RegistryError, ex, sys.exc_info()[2]
            if isinstance(value, type) and should_fix_type(value):
                value.__module__ = self.module_name
            self._accessed = True
            self._value = value

        return self._value

    def assign(self, value):
        if self.is_accesed:
            filename, line, name, text = '?', '?', '?', '?'
            if self._access_traceback is not None:
                filename, line, name, text = self._access_traceback[-3]
            raise RegistryError(
                "Cannot assign '%s'. "
                "Was already accessed by "
                "%s:%s %s '%s'" % (
                    self.name,
                    filename,
                    line,
                    name,
                    text))
        self._value = value


class BaseModule(ModuleType):

    _imports = None
    _imported_attrs = None
    _modules = {}

    def __new__(cls, fullname):
        if fullname in cls._modules:
            raise Exception()
        module = super(BaseModule, cls).__new__(cls, fullname)
        cls._modules[fullname] = module
        return module

    def __init__(self, fullname):
        super(BaseModule, self).__init__(fullname)
        self._attrs = {}

    def _import(self):
        if self._imported_attrs is None:
            self._imported_attrs = {}
            if self._imports:
                module = import_module(self._imports)
                self._imported_attrs.update(
                    **{
                        name: value
                        for name, value in six.iteritems(vars(module))
                        if not name.startswith('_')
                    }
                )

    def __getattribute__(self, name):
        if name.startswith('_'):
            # Fall back to original behaviour
            try:
                return super(BaseModule, self).__getattribute__(name)
            except AttributeError:
                pass
        elif not self[name].is_assigned:
            # Fall back to original behaviour
            try:
                value = super(BaseModule, self).__getattribute__(name)
            except AttributeError:
                # Import now
                self._import()
                if name in self._imported_attrs:
                    self[name].assign(self._imported_attrs[name])
            else:
                self[name].assign(value)

        if self[name].is_assigned:
            return self[name].access()

        raise AttributeError(name)

    @property
    def __all__(self):
        names = set()
        for name in six.iterkeys(self._attrs):
            names.add(name)
        for name in six.iterkeys(self._base_attrs):
            names.add(name)
        return list(names)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
        else:
            self[name].assign(value)

    def __getitem__(self, name):
        if name not in self._attrs:
            self._attrs[name] = ModuleAttribute(self.__name__, name)
        return self._attrs[name]

    @classmethod
    def imports(cls, module):
        return type('Module', (cls, ), {'_imports': module})

    @classmethod
    def find_module(cls, fullname, path=None):
        if fullname in cls._modules:
            return cls

    @classmethod
    def load_module(cls, fullname):
        module = cls._modules[fullname]
        module.__loader__ = cls
        module.__file__ = "<%s>" % cls.__name__
        module.__package__ = fullname.rpartition('.')[0]
        module._import()
        sys.modules.setdefault(fullname, module)
        return module
