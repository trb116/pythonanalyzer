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


class TopologicalSortError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "{0}({1})".format(self.__class__.__name__, self.message)


def topological_sort(graph):
    """
    Performs a dependency based topological sort. Keeping a stable order.

    Arguments:
        - graph: An (ordered) dictionary representing a directed graph. Where each item
        is { node: [set or list of incomming edges (depedencies)] }
    """

    # Copy graph for lookup purposes
    incomming = OrderedDict(
        [
            (node, list(edges)) for node, edges in graph.iteritems()
        ]
    )

    # Try to output nodes in initial order
    nodes = [node for node in incomming.iterkeys()]

    # Keep a stack in order to detect cyclic dependencies
    stack = []
    while nodes:
        # Get first node
        n = nodes[0]

        # See if this node has dependencies which haven't yet been
        # outputted.
        remaining = [node for node in reversed(incomming[n]) if node in nodes]
        if remaining:
            if n not in stack:
                stack.append(n)
            else:
                raise TopologicalSortError(
                    "Cyclic dependency"
                    " detected {0}".format(
                        '->'.join(
                            [
                                str(x) for x in (
                                    stack + [n]
                                )
                            ]
                        )
                    )
                )
            for m in remaining:
                # Place dependency at front
                nodes.remove(m)
                nodes.insert(0, m)
        else:
            # No dependencies left, output
            yield nodes.pop(0)
