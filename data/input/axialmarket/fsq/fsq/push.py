# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Jeff Rand <jeff.rand@axial.net>
#
# fsq/push.py -- provides remote distsitrubtion function: push
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
# This software is for POSIX compliant systems only.
from jsonrpclib import Server
from . import FSQPushError, FSQRemoteTriggerError, constants as _c

def push(item, remote_addr, trg_queue, protocol=u'jsonrpc'):
    ''' Enqueue an FSQWorkItem at a remote queue '''
    if protocol == u'jsonrpc':
        try:
            server = Server(remote_addr, encoding=_c.FSQ_CHARSET)
            return server.enqueue(item.id, trg_queue, item.item.read())
        except Exception, e:
            raise FSQPushError(e)

    raise ValueError('Unknown protocol: {0}'.format(protocol))

def remote_trigger_pull(remote_addr, trg_queue, ignore_listener=False,
                        protocol=u'jsonrpc'):
    '''Write a non-blocking byte to a remote trigger fifo, to cause a triggered
       scan'''
    if protocol == u'jsonrpc':
        try:
            server = Server(remote_addr, encoding=_c.FSQ_CHARSET)
            return server.trigger_pull(queue=trg_queue,
                                       ignore_listener=ignore_listener,
                                       trigger=_c.FSQ_TRIGGER)
        except Exception, e:
            raise FSQRemoteTriggerError(e)

    raise ValueError('Unknown protocol: {0}'.format(protocol))
