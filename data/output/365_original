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

from collections import OrderedDict

from sellmo.utils.sorting import topological_sort


class Loader(object):
    def __init__(self):
        self._graph = OrderedDict()
        self._actions = dict() # Maps actions to loadables
        self._funcs = dict() # Maps functions to loadables

    def _register_or_get_loadable(self, func=None, action=None):
        # We attempt to get or create a loadable by an action name.
        # Else we fall back to func.
        if action is not None and action in self._actions:
            # A loadable already exists for this action
            loadable = self._actions[action]
        elif func is not None and func in self._funcs:
            # A loadable already exists for this function
            loadable = self._funcs[func]
        else:
            if action is not None:
                # Create a new loadable for the given action
                loadable = Loadable(action=action)
            elif func is not None:
                # Create a new loadable for the given func
                loadable = Loadable(func=func)
            else:
                raise Exception()

            # Extend graph
            self._graph[loadable] = []

        # Update or create mappings
        if action is not None:
            self._actions[action] = loadable

        if func is not None:
            existing = self._funcs.get(func, None)
            if existing is not None and existing != loadable:
                raise Exception(
                    "Too late to register function %s "
                    "@load(action='%s') needs to be "
                    "the first decorator." % (func, action)
                )
            self._funcs[func] = loadable

        return loadable

    def register(self, func, action=None, after=None, before=None):
        loadable = self._register_or_get_loadable(func=func, action=action)
        if func not in loadable.funcs:
            loadable.funcs.append(func)

        # Handle after and before, first make sure a loadable is
        # present. If not create a placeholder loadable.
        if after is not None:
            after = self._register_or_get_loadable(action=after)
            self._graph[loadable].append(after)

        if before is not None:
            before = self._register_or_get_loadable(action=before)
            self._graph[before].append(loadable)

    def load(self):
        for loadable in topological_sort(self._graph):
            for func in loadable.funcs:
                func()


class Loadable(object):
    def __init__(self, func=None, action=None):
        self._func = func
        self._action = action
        self.funcs = []

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        if self._action:
            return hash(self._action)
        if self._func:
            return hash(self._func)

    def __repr__(self):
        if self._action:
            return "{0}".format(self._action)
        if self._func:
            return (
                "{0}.{1}".format(
                    self._func.__module__, self._func.__name__
                )
            )


loader = Loader()
