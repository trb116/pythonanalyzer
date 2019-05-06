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

import abc


class AbstractProcessStep(object):

    __metaclass__ = abc.ABCMeta

    key = None
    process = None
    _previous_step = None

    def __init__(self, key=None):
        if key:
            self.key = key
        if self.key is None:
            raise ValueError("Key for this step is not given")

    def hookup(self, process):
        self.process = process

    @property
    def url(self):
        return self.resolve_url()

    @property
    def has_deviated(self):
        """
        Indicates if this step has deviated from the
        process's path, this will cause the process to
        rewind after this step has completed.
        """
        return False

    @abc.abstractproperty
    def is_completed(self):
        """
        Indicates if this step is completed successfully.
        """
        pass

    @property
    def can_skip(self):
        """
        Indicates if this step can be visited again.
        """
        return False

    @property
    def is_definitive(self):
        """
        Indicates if this step can be visited again.
        """
        return False

    @abc.abstractmethod
    def complete(self, request, data, *args, **kwargs):
        """
        Attempts to complete this step with the given data.
        """
        pass

    @abc.abstractmethod
    def render(self, request, *args, **kwargs):
        """
        Renders this step in it's current state.
        """
        pass

    @abc.abstractmethod
    def resolve_url(self):
        """
        Resolves the url for this step.
        """
        return self.process.resolve_url(self)

    def get_next_step(self):
        """
        Returns the next step (if any).
        """
        return None
