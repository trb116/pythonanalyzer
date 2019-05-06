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
import inspect

from django.core.checks import register

from sellmo.utils.decorator import NO_ARGS, no_args_decorator

from .chains import Chain

_chains = []


def link(target, binds=False, takes_result=False, provides=None, prepend=False):
    """
    Link function to the given chain
    """

    chain = target
    if inspect.ismethod(target):
        # Dealing with a bound function
        chain = target.im_func

    if not isinstance(chain, Chain):
        if hasattr(chain, '_chain'):
            chain = chain._chain
        else:
            raise ValueError(
                'Function <%s.%s> is not a chain' %
                (target.__module__, target.__name__)
            )

    def decorator(func):
        chain.link(
            func,
            binds=binds,
            takes_result=takes_result,
            provides=provides,
            prepend=prepend
        )

        return func

    return decorator


def define(no_args=NO_ARGS, cls=Chain, binds=False, takes_result=False, provides=None):
    """
    Defines a new chain
    """

    def decorator(func):
        chain = cls(func, binds=binds, takes_result=takes_result, provides=provides)
        _chains.append(chain)

        def wrapper(*args, **kwargs):
            # Use __traceback_hide__ which is used by a few libraries
            # to hide internal frames. Django supports this.
            __traceback_hide__ = True # NOQA
            return chain(*args, **kwargs)

        wrapper._chain = chain
        functools.update_wrapper(wrapper, func)
        return wrapper

    return no_args_decorator(decorator, no_args)


@register
def _check_chains(app_configs, **kwargs):
    errors = []
    for chain in _chains:
        errors.extend(chain.check())
    return errors
