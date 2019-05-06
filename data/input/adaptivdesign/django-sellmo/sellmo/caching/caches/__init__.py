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

from django.core.cache import caches
from django.utils.module_loading import import_string

from sellmo.conf import get_setting
from sellmo.caching.constants import DEFAULT_CACHE_ALIAS

from .base import BaseCache

CACHES = get_setting(
    'CACHES',
    default={
        'django.core.cache.backends.locmem.LocMemCache':
        'sellmo.caching.caches.locmem.LocMemCache',
        'django_redis.cache.RedisCache':
        'sellmo.caching.caches.redis.RedisCache',
    }
)

backend_cls = type(caches[DEFAULT_CACHE_ALIAS])


def cache_factory():
    dotted_path = '%s.%s' % (backend_cls.__module__, backend_cls.__name__)
    if dotted_path in CACHES:
        return import_string(CACHES[dotted_path])
    return BaseCache


class Cache(cache_factory()):
    pass


class ChainCache(cache_factory()):
    def __init__(self, func, **kwargs):
        super(ChainCache, self).__init__(**kwargs)
        func._chain.link(self.catch, binds=True, prepend=True)

    def catch(self, *args, **kwargs):
        raise NotImplementedError()
