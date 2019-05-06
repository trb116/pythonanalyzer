# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Matthew Story <matt.story@axial.net>
# @author: Jeff Rand <jeff.rand@axial.net>
#
# fsq/items.py -- provides items classes for fsq: FSQItem, FSQEnqueueItem
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
# This software is for POSIX compliant systems only.
import errno
import datetime

from . import constants as _c, path as fsq_path, deconstruct,\
              FSQMalformedEntryError, FSQTimeFmtError, FSQWorkItemError,\
              FSQMaxTriesError, FSQTTLExpiredError, fail, success, done,\
              fail_tmp, fail_perm
from .internal import rationalize_file, wrap_io_os_err, check_ttl_max_tries

class FSQEnqueueItem(object):
    '''Stub for Streamable Enqueue object, e.g.

        foo = FSQEnqueueItem('foo', 'bar', 'baz', 'bang')
        try:
            for i in ['a', 'b', 'c']:
                foo.item.write(i)
            foo.commit()
        except Exception, e:
            foo.abort()
        finally:
            del foo
    '''
    pass

class FSQWorkItem(object):
    '''An FSQWorkItem object.  FSQWorkItem stores an open and potentially
       exclusive-locked file to a work file as the attribute self.item, opened
       in read-only mode.

       FSQWorkItem is intended to a minimalist object, capable of reverse
       engineering to a C struct.  The C struct will support all attributes,
       but the methods will not be available, they will be available as
       include level functions taking a *WorkItem struct as their first
       argument.

       BEWARE: If you choose not to lock, the item you are working on may be
       worked on by others, and may be moved (on failure or success) out from
       underneath you.  Should you send lock=False, it is assumed you are
       guarenteeing concurrency of 1 on the queue through some other
       mechanism.'''
    ####### MAGICAL METHODS AND ATTRS #######
    def __init__(self, trg_queue, item_id, max_tries=None, ttl=None,
                 lock=None, no_open=False, host=None):
        '''Construct an FSQWorkItem object from an item_id (file-name), and
           queue-name.  The lock kwarg will override the default locking
           preference (taken from environment).'''

        self.id = item_id
        self.queue = trg_queue
        self.max_tries = _c.FSQ_MAX_TRIES if max_tries is None else max_tries
        self.ttl = _c.FSQ_TTL if ttl is None else ttl
        self.lock = _c.FSQ_LOCK if lock is None else lock
        self.item = None
        self.host = host

        # open file immediately
        if not no_open:
            self.open()
        try:
            self.delimiter, arguments = deconstruct(item_id)
            try:
                # construct datetime.datetime from enqueued_at
                self.enqueued_at = datetime.datetime.strptime(arguments[0],
                                                              _c.FSQ_TIMEFMT)
                self.entropy = arguments[1]
                self.pid = arguments[2]
                self.hostname = arguments[3]
                self.tries = arguments[4]
                self.arguments = tuple(arguments[5:])
            except IndexError, e:
                raise FSQMalformedEntryError(errno.EINVAL, u'needed at least'\
                                             u' 4 arguments to unpack, got:'\
                                             u' {0}'.format(len(arguments)))
            except ValueError, e:
                raise FSQTimeFmtError(errno.EINVAL, u'invalid date string'\
                                      u' for strptime fmt {0}:'\
                                      u' {1}'.format(_c.FSQ_TIMEFMT,
                                                     arguments[0]))
            try:
                self.tries = int(self.tries)
            except ValueError, e:
                raise FSQTimeFmtError(errno.EINVAL, u'tries must be an int,'\
                                      u' not {0}: {1}'.format(
                                        self.tries.__class__.__name__,
                                        self.tries))
            try:
                check_ttl_max_tries(self.tries, self.enqueued_at,
                                    self.max_tries, self.ttl)
            except (FSQMaxTriesError, FSQTTLExpiredError, ), e:
                e.strerror = u': '.join([
                    e.strerror,
                    u'for item {0}; failed permanently'.format(self.id),
                ])
                raise e
        except Exception, e:
            try:
                # unhandled exceptions are perm failures
                self.fail_perm()
            finally:
                self.close()
            raise e

    def __del__(self):
        '''Always close the file when the ref count drops to 0'''
        self.close()


    ####### EXPOSED METHODS AND ATTRS #######
    def close(self):
        # TODO : Why not just check to instance of file object?
        if (hasattr(self, 'item') and hasattr(self.item, 'close')
                and self.item is not None):

            self.item.close()

    def open(self):
        self.close()
        try:
            self.item = rationalize_file(fsq_path.item(self.queue, self.id,
                                                       host=self.host),
                                         _c.FSQ_CHARSET, lock=self.lock)
        except (OSError, IOError, ), e:
            if e.errno == errno.ENOENT:
                raise FSQWorkItemError(e.errno, u'no such item in queue {0}:'\
                                       u' {1}'.format(self.queue, self.id))
            raise FSQWorkItemError(e.errno, wrap_io_os_err(e))

    def done(self, done_type=None):
        '''Complete an item, either successfully or with failure'''
        return done(self, done_type)

    def success(self):
        '''Complete an item successfully'''
        return success(self)

    def fail(self, fail_type=None):
        '''Fail this item either temporarily or permanently.'''
        return fail(self, fail_type)

    def fail_tmp(self):
        '''Fail an item temporarily (either retry, or escalate to perm)'''
        return fail_tmp(self)

    def fail_perm(self):
        return fail_perm(self)
