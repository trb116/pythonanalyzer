# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Matthew Story <matt.story@axial.net>
# @author: Jeff Rand <jeff.rand@axial.net>
#
# fsq/done.py -- provides finishing functions: done, fail, fail_tmp,
#                   fail_perm, retry
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
# This software is for POSIX compliant systems only.
import os
from . import constants as _c, FSQDoneError, FSQFailError, FSQMaxTriesError,\
              FSQEnqueueError, FSQTTLExpiredError, path as fsq_path, construct
from .internal import wrap_io_os_err, check_ttl_max_tries, fmt_time

####### EXPOSED METHODS #######
def fail_tmp(item, max_tries=None, ttl=None):
    '''Try to fail a work-item temporarily (up recount and keep in queue),
       if max tries or ttl is exhausted, escalate to permanant failure.'''
    try:
        max_tries = item.max_tries if max_tries is None else max_tries
        ttl = item.ttl if ttl is None else ttl

        # see if we need to fail perm
        check_ttl_max_tries(item.tries+1, item.enqueued_at, max_tries, ttl)
        # mv to same plus 1
        item.tries += 1
        new_name = construct(( fmt_time(item.enqueued_at, _c.FSQ_TIMEFMT,
                               _c.FSQ_CHARSET), item.entropy,
                               item.pid, item.hostname,
                               item.tries, ) + tuple(item.arguments))
        os.rename(fsq_path.item(item.queue, item.id, host=item.host),
				  fsq_path.item(item.queue, new_name, host=item.host))
        return new_name
    except (FSQMaxTriesError, FSQTTLExpiredError, FSQEnqueueError, ), e:
        fail_perm(item)
        e.strerror = u': '.join([
            e.strerror,
            u'for item {0}; failed permanently'.format(item.id),
        ])
        raise e

def fail_perm(item):
    '''Fail a work-item permanatly by mv'ing it to queue's fail directory'''
    # The only thing we require to fail is an item_id and a queue
    # as an item may fail permanently due to malformed item_id-ness
    item_id = item.id
    trg_queue = item.queue
    host = item.host
    try:
        os.rename(fsq_path.item(trg_queue, item_id, host=host),
                  os.path.join(fsq_path.fail(trg_queue, host=host), item_id))
    except (OSError, IOError, ), e:
        raise FSQFailError(e.errno, u'cannot mv item to fail: {0}:'\
                           u' {1}'.format(item.id, wrap_io_os_err(e)))

    return item.id

def done(item, done_type=None, max_tries=None, ttl=None):
    '''Wrapper for any type of finish, successful, permanant failure or
       temporary failure'''
    if done_type is None or done_type == _c.FSQ_SUCCESS:
        return success(item)
    return fail(item, fail_type=done_type, max_tries=max_tries, ttl=ttl)

def fail(item, fail_type=None, max_tries=None, ttl=None):
    '''Fail a work item, either temporarily or permanently'''
    # default to fail_perm
    if fail_type is not None and fail_type == _c.FSQ_FAIL_TMP:
        return fail_tmp(item, max_tries=max_tries, ttl=ttl)
    return fail_perm(item)

def success(item):
    '''Successful finish'''
    try:
        # mv to done
        trg_queue = item.queue
        os.rename(fsq_path.item(trg_queue, item.id, host=item.host),
                  os.path.join(fsq_path.done(trg_queue, host=item.host),
                               item.id))
    except AttributeError, e:
        # DuckType TypeError'ing
        raise TypeError(u'item must be an FSQWorkItem, not:'\
                        u' {0}'.format(item.__class__.__name__))
    except (OSError, IOError, ), e:
        raise FSQDoneError(e.errno, u'cannot mv item to done: {0}:'\
                           u' {1}'.format(item.id, wrap_io_os_err(e)))

def retry(*args, **kwargs):
    '''Retry is a convenience alias for fail_tmp'''
    return fail_tmp(*args, **kwargs)
