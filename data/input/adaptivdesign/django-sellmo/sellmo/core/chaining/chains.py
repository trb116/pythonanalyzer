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

import functools

from .execution import Execution, ExecutableFunc


class Chain(object):
    def __init__(self, func, binds=False, takes_result=False, provides=None):
        self._chain = self
        self._is_finalized = False
        self._execution = self.execution_factory()(
            ExecutableFunc(
                func,
                binds=binds,
                takes_result=takes_result,
                provides=provides
            )
        )

    def execution_factory(self):
        return Execution

    def link(self, func, binds=False, takes_result=False, provides=None, prepend=False):
        executable = ExecutableFunc(
            func,
            binds=binds,
            takes_result=takes_result,
            provides=provides
        )

        if prepend:
            self._execution.prepend(executable)
        else:
            self._execution.add(executable)

    def _finalize(self):
        self._is_finalized = self._execution.compile()
        functools.update_wrapper(self, self._execution)

    def __call__(self, *args, **kwargs):
        if not self._is_finalized:
            self._finalize()
        # Use __traceback_hide__ which is used by a few libraries
        # to hide internal frames. Django supports this.
        __traceback_hide__ = True
        return self._execution(*args, **kwargs)

    def check(self):
        if not self._is_finalized:
            self._finalize()
        return self._execution.errors

    def __repr__(self):
        return 'chain: %s' % repr(self._signature_func)
