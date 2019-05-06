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

from django.utils import six
from django.utils.encoding import smart_str

if six.PY3:
    from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode
else:
    from urlparse import urlparse, parse_qsl, urlunparse
    from urllib import urlencode


class QueryString(object):
    def __init__(self, request=None):
        self.params = {}
        if request:
            for key in request.GET.keys():
                self[key] = request.GET.getlist(key)

    def __contains__(self, param):
        if isinstance(param, tuple):
            return param[1] in self.params.get(param[0], set())
        else:
            return param in self.params

    def add_param(self, key, value):
        self[key] = list(self.get_param(key, [])) + [value]

    def remove_param(self, key, value=None):
        if key not in self.params:
            raise ValueError("No such param {0}".format(key))
        if value is not None:
            if value not in self.params[key]:
                raise ValueError("No such param {0}, {1}".format(key, value))
            self.params[key].remove(value)
        else:
            del self.params[key]

    def set_param(self, key, value):
        self[key] = value

    def get_param(self, param, default=None):
        if param in self:
            return self[param]
        return default

    def __getitem__(self, key):
        return frozenset(self.params[key])

    def __setitem__(self, key, value):
        if not isinstance(value, (tuple, list, set)):
            value = [value]
        self.params[key] = set([smart_str(el) for el in value if el])

    def __iter__(self):
        for key in self.params.keys():
            yield key, self[key]

    def __repr__(self):
        params = []
        for key, values in self:
            for value in values:
                value = smart_str(value)
                params.append((key, value))
        return urlencode(params)

    def __le__(self, other):
        for key in self.params.keys():
            if key not in other.params:
                return False
            if not self.params[key] <= other.params[key]:
                return False
        return True

    def __ge__(self, other):
        for key in other.params.keys():
            if key not in self.params:
                return False
            if not self.params[key] >= other.params[key]:
                return False
        return True

    def __eq__(self, other):
        if set(self.params.keys()) != set(other.params.keys()):
            return False
        for key in self.params.keys():
            if not self.params[key] == other.params[key]:
                return False
        return True

    def __nonzero__(self):
        return bool(self.params)

    def clone(self):
        clone = QueryString()
        clone.params = {key: set(value) for key, value in self}
        return clone
