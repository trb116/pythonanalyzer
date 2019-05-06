# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Jeff Rand <jeff.rand@axial.net>
#
# fsq/v1.py -- provides version 1 API function: enqueue
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
# This software is for POSIX compliant systems only.
from .. import vsreenqueue, trigger_pull, is_down

def enqueue(fsq_id, trg_queue, data):
    ''' Enqueue an item pushed from a remote client '''
    return vsreenqueue(fsq_id, data, [ trg_queue, ])

#libexec/fsq/jsonrpcd.py will load all functions in __all__
__all__ = [ 'enqueue', 'trigger_pull', 'is_down', ]
