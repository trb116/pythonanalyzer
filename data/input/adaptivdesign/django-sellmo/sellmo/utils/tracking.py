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

import types

from django.db import models


class UntrackableError(Exception):
    pass


class TrackableQuerySet(models.QuerySet):
    def try_get_tracked(self, request):
        if self.model.is_tracked(request):
            try:
                return self.get(pk=self.model.get_tracked_pk(request))
            except self.model.DoesNotExist:
                pass
        return self.model()


class TrackableManager(models.Manager):
    pass


class TrackableModel(models.Model):

    _session_key = None

    @classmethod
    def is_tracked(cls, request):
        return cls._session_key in request.session

    @classmethod
    def get_tracked_pk(cls, request):
        return request.session[cls._session_key]

    def track(self, request):
        if self.pk is None:
            raise UntrackableError("Cannot track non persistent object")
        request.session[self._session_key] = self.pk

    def untrack(self, request):
        request.session.pop(self._session_key, None)

    class Meta:
        abstract = True
