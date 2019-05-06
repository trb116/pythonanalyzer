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

from django.utils import six

from .exceptions import ExecutionError


class AbstractExecutionInstruction(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def handle(self, state, stack, call):
        pass


class DefaultInstruction(AbstractExecutionInstruction):
    def handle(self, state, stack, call):
        if not call.is_exhausted:
            stack.append(call)


class ForwardInstruction(DefaultInstruction):
    """
    Move forward and return at this point once
    all following sub calls are done.
    """

    def handle(self, state, stack, call):
        # Clone the current stack
        new_stack = stack.clone()
        super(ForwardInstruction, self).handle(state, stack, call)
        return new_stack


class InterruptInstruction(DefaultInstruction):
    """
    Interrupt any following sub calls.
    """

    def handle(self, state, stack, call):
        # Exhaust all remaining calls in stack
        for next_call in stack:
            if next_call != call:
                next_call.exhaust()

        # Clear the current stack
        stack.clear()

        # But still allow our call
        # to finish.
        super(InterruptInstruction, self).handle(state, stack, call)


class UpdateKwargsInstruction(DefaultInstruction):
    """
    Instructs the execution to update the given kwargs to be used for further
    function calls.
    """

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def handle(self, state, stack, call):
        super(UpdateKwargsInstruction, self).handle(state, stack, call)
        state.kwargs.update(self._kwargs)


class WaitInstruction(AbstractExecutionInstruction):
    def handle(self, state, stack, call):
        # Simply do nothing, do not put our call back.
        pass


class ExitInstruction(AbstractExecutionInstruction):
    """
    Completely exit the current execution.
    """

    def handle(self, state, stack, call):
        return False
