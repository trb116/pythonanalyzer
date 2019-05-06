# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Matthew Story <matt.story@axial.net>
# @author: Jeff Rand <jeff.rand@axial.net>
#
# fsq/enqueue.py -- provides enqueueing functions: enqueue, senqueue,
#                   venqueue, vsenqueue, reenqueue, sreenqueue, vreenqueue,
#                   vsreenqueue
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
# This software is for POSIX compliant systems only.
import errno
import os
import datetime
import socket
import select

from cStringIO import StringIO
from contextlib import closing

from . import FSQEnqueueError, FSQCoerceError, FSQError, FSQReenqueueError,\
              constants as _c, path as fsq_path, construct,\
              hosts as fsq_hosts, FSQWorkItem
from .internal import rationalize_file, wrap_io_os_err, fmt_time,\
                      coerce_unicode, uid_gid

# TODO: provide an internal/external streamable queue item object use that
#       instead of this for the enqueue family of functions
#       make a queue item from args, return a file

####### INTERNAL MODULE FUNCTIONS AND ATTRIBUTES #######
_HOSTNAME = socket.gethostname()
_ENTROPY_PID = None
_ENTROPY_TIME = None
_ENTROPY_HOST = None
_ENTROPY = 0

# sacrifice a lot of complexity for a little statefullness
def _mkentropy(pid, now, host):
    global _ENTROPY_PID, _ENTROPY_TIME, _ENTROPY_HOST, _ENTROPY
    if _ENTROPY_PID == pid and _ENTROPY_TIME == now and _ENTROPY_HOST == host:
        _ENTROPY += 1
    else:
        _ENTROPY_PID = pid
        _ENTROPY_TIME = now
        _ENTROPY_HOST = host
        _ENTROPY = 0
    return _ENTROPY

def _formhostpath(args, hosts, all_hosts):
    path = []
    if not hosts and not all_hosts:
        for arg in args:
            path.append((arg, None))
    else:
        for arg in args:
            if all_hosts:
                hosts = fsq_hosts(arg)
            for host in hosts:
                path.append((arg, host))
    return tuple(path)

def _unpack_args(item_f, src_queue, link, args):
    if isinstance(item_f, FSQWorkItem):
        item_id = item_f.id
        src_queue = item_f.queue
        item_f = item_f.item
    elif src_queue:
        item_id = coerce_unicode(item_f, _c.FSQ_CHARSET)
        item_f = None
    else:
        args = list(args)
        if link:
            raise ValueError('Incorrect arguments')
        try:
            item_id = args.pop(0)
        except IndexError:
            raise ValueError('Insufficient arguments')
    return item_f, src_queue, item_id , args, link

####### EXPOSED METHODS #######
def enqueue(trg_queue, item_f, *args, **kwargs):
    '''Enqueue the contents of a file, or file-like object, file-descriptor or
       the contents of a file at an address (e.g. '/my/file') queue with
       arbitrary arguments, enqueue is to venqueue what printf is to vprintf
    '''
    return venqueue(trg_queue, item_f, args, **kwargs)

def senqueue(trg_queue, item_s, *args, **kwargs):
    '''Enqueue a string, or string-like object to queue with arbitrary
       arguments, senqueue is to enqueue what sprintf is to printf, senqueue
       is to vsenqueue what sprintf is to vsprintf.
    '''
    return vsenqueue(trg_queue, item_s, args, **kwargs)

def venqueue(trg_queue, item_f, args, user=None, group=None, mode=None):
    '''Enqueue the contents of a file, or file-like object, file-descriptor or
       the contents of a file at an address (e.g. '/my/file') queue with
       an argument list, venqueue is to enqueue what vprintf is to printf

       If entropy is passed in, failure on duplicates is raised to the caller,
       if entropy is not passed in, venqueue will increment entropy until it
       can create the queue item.
    '''
    # setup defaults
    trg_fd = name = None
    user = _c.FSQ_ITEM_USER if user is None else user
    group = _c.FSQ_ITEM_GROUP if group is None else group
    mode = _c.FSQ_ITEM_MODE if mode is None else mode
    now = fmt_time(datetime.datetime.now(), _c.FSQ_TIMEFMT, _c.FSQ_CHARSET)
    pid = coerce_unicode(os.getpid(), _c.FSQ_CHARSET)
    host = coerce_unicode(_HOSTNAME, _c.FSQ_CHARSET)
    tries = u'0'
    entropy = _mkentropy(pid, now, host)

    # open source file
    try:
        src_file = rationalize_file(item_f, _c.FSQ_CHARSET)
    except (OSError, IOError, ), e:
        raise FSQEnqueueError(e.errno, wrap_io_os_err(e))
    try:
        real_file = True if hasattr(src_file, 'fileno') else False
        # get low, so we can use some handy options; man 2 open
        try:
            item_name = construct(( now, entropy, pid, host,
                                    tries, ) + tuple(args))
            tmp_name = os.path.join(fsq_path.tmp(trg_queue), item_name)
            trg_fd = os.open(tmp_name, os.O_WRONLY|os.O_CREAT|os.O_EXCL, mode)
        except (OSError, IOError, ), e:
            if isinstance(e, FSQError):
                raise e
            raise FSQEnqueueError(e.errno, wrap_io_os_err(e))
        try:
            if user is not None or group is not None:
                # set user/group ownership for file; man 2 fchown
                os.fchown(trg_fd, *uid_gid(user, group, fd=trg_fd))
            with closing(os.fdopen(trg_fd, 'wb', 1)) as trg_file:
                # i/o time ... assume line-buffered
                while True:
                    if real_file:
                        reads, dis, card = select.select([src_file], [], [])
                        try:
                            msg = os.read(reads[0].fileno(), 2048)
                            if 0 == len(msg):
                                break
                        except (OSError, IOError, ), e:
                            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN,):
                                continue
                            raise e
                        trg_file.write(msg)
                    else:
                        line = src_file.readline()
                        if not line:
                            break
                        trg_file.write(line)

                # flush buffers, and force write to disk pre mv.
                trg_file.flush()
                os.fsync(trg_file.fileno())

                # hard-link into queue, unlink tmp, failure case here leaves
                # cruft in tmp, but no race condition into queue
                os.link(tmp_name, os.path.join(fsq_path.item(trg_queue,
                                                            item_name)))
                os.unlink(tmp_name)

                # return the queue item id (filename)
                return item_name
        except Exception, e:
            try:
                os.close(trg_fd)
            except (OSError, IOError, ), err:
                if err.errno != errno.EBADF:
                    raise FSQEnqueueError(err.errno, wrap_io_os_err(err))
            try:
                if tmp_name is not None:
                    os.unlink(tmp_name)
            except (OSError, IOError, ), err:
                if err.errno != errno.ENOENT:
                   raise FSQEnqueueError(err.errno, wrap_io_os_err(err))
            try:
                if name is not None:
                    os.unlink(name)
            except OSError, err:
                if err.errno != errno.ENOENT:
                   raise FSQEnqueueError(err.errno, wrap_io_os_err(err))
            if (isinstance(e, OSError) or isinstance(e, IOError)) and\
                    not isinstance(e, FSQError):
                raise FSQEnqueueError(e.errno, wrap_io_os_err(e))
            raise e
    finally:
        src_file.close()

def vsenqueue(trg_queue, item_s, args, **kwargs):
    '''Enqueue a string, or string-like object to queue with arbitrary
       arguments, vsenqueue is to venqueue what vsprintf is to vprintf,
       vsenqueue is to senqueue what vsprintf is to sprintf.
    '''
    charset = kwargs.get('charset', _c.FSQ_CHARSET)
    if kwargs.has_key('charset'):
        del kwargs['charset']

    # we coerce here because StringIO.StringIO will coerce on file-write,
    # and cStringIO.StringIO has a bug which injects NULs for unicode
    if isinstance(item_s, unicode):
        try:
            item_s = item_s.encode(charset)
        except UnicodeEncodeError:
            raise FSQCoerceError(errno.EINVAL, u'cannot encode item with'\
                                 u' charset {0}'.format(charset))

    return venqueue(trg_queue, StringIO(item_s), args, **kwargs)

def reenqueue(item_f, *args, **kwargs):
    '''Enqueue the contents of a file, or file-like object, FSQWorkItem,
       file-descriptor or the contents of a files queues at an address
       (e.g. '/my/file') queue with arbitrary arguments from one queue to
       other queues, reenqueue is to vreenqueue what printf is to vprintf
    '''
    src_queue = kwargs.pop('src_queue', None)
    link = kwargs.pop('link', False)
    if isinstance(item_f, FSQWorkItem):
        return vreenqueue(item_f, args, link=link, **kwargs)
    item_f, src_queue, item_id, args, link = _unpack_args(item_f, src_queue,
                                                          link, args)
    if not item_f:
        return vreenqueue(item_id, args, src_queue=src_queue, link=link,
                          **kwargs)
    return vreenqueue(item_f, item_id, args, src_queue=src_queue, link=link,
                      **kwargs)

def vreenqueue(item_f, *args, **kwargs):
    '''Enqueue the contents of a file, or file-like object, FSQWorkItem,
       file-descriptor or the contents of a files queues at an address
       (e.g. '/my/file') queue with arbitrary arguments from one queue to
       other queues, reenqueue is to vreenqueue what printf is to vprintf
       Uses include:
            vreenqueue(FSQWorkItem, [trg_queue, ...], link=, kwargs)
            vreenqueue(fileish, file_name, [trg_queue, ...], kwargs)
            vreenqueue(fd, file_name, [trg_queue, ...], kwargs)
    '''
    item_id = None
    src_queue = kwargs.pop('src_queue', None)
    link = kwargs.pop('link', False)
    hosts = kwargs.pop('hosts', None)
    all_hosts = kwargs.pop('all_hosts', False)
    item_f, src_queue, item_id, args, link = _unpack_args(item_f, src_queue,
                                                          link, args)
    if 1 < len(args):
        raise ValueError('Too many arguements')
    try:
        args = args[0]
    except IndexError:
        raise ValueError('Insufficient arguments')
    try:
        if item_f is None:
            item_f = fsq_path.item(src_queue, item_id)
        if link:
            src_file = item_f
        else:
            src_file = rationalize_file(item_f, _c.FSQ_CHARSET)
    except (OSError, IOError, ), e:
        raise FSQReenqueueError(e.errno, wrap_io_os_err(e))
    tmp_names = []
    try:
        paths = _formhostpath(args, hosts, all_hosts)
        if link:
            tmp_name = os.path.join(fsq_path.tmp(src_queue), item_id)
            # hard link directly to tmp
            try:
                try:
                    os.link(fsq_path.item(src_queue, item_id), tmp_name)
                except (OSError, IOError, ), e:
                    if not e.errno == errno.EEXIST:
                        raise FSQReenqueueError(e.errno, wrap_io_os_err(e))
                for queue, host in paths:
                    try:
                        os.link(tmp_name, os.path.join(fsq_path.item(queue,
                                                       item_id, host=host)))
                    except (OSError, IOError, ), e:
                        if not e.errno == errno.EEXIST:
                            raise FSQReenqueueError(e.errno, wrap_io_os_err(e))
            finally:
                os.unlink(tmp_name)
        else:
            tmp_fos = []
            try:
                for queue, host in paths:
                    try:
                        tmp_name = os.path.join(fsq_path.tmp(queue, host=host),
                                                             item_id)
                        tmp_names.append(tmp_name)
                        # copy to n trg_queues
                        tmp_fo = os.open(tmp_name, os.O_RDWR|os.O_CREAT|\
                                               os.O_TRUNC, _c.FSQ_ITEM_MODE)
                        tmp_fos.append(os.fdopen(tmp_fo, 'wb', 1))
                    except Exception, e:
                        raise FSQReenqueueError(wrap_io_os_err(e))
                real_file = True if hasattr(src_file, 'fileno') else False
                # read src_file once
                while True:
                    if real_file:
                        reads, dis, card = select.select([src_file], [], [])
                        try:
                            chunk = os.read(reads[0].fileno(), 2048)
                        except (OSError, IOError, ), e:
                            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN,):
                                continue
                            raise
                    else:
                        chunk = src_file.readline()
                    if 0 == len(chunk):
                        break
                    for tmp_fo in tmp_fos:
                        tmp_fo.write(chunk)
                        # flush buffers, and force write to disk pre mv.
                        tmp_fo.flush()
                        os.fsync(tmp_fo.fileno())
                for queue, host in paths:
                    tmp_name = os.path.join(fsq_path.tmp(queue, host=host),
                                                         item_id)
                    # hard-link into queue, unlink tmp, failure case here
                    # leaves cruft in tmp, but no race condition into queue
                    try:
                        os.link(tmp_name, os.path.join(fsq_path.item(queue,
                                                       item_id, host=host)))
                    except (OSError, IOError, ), e:
                        if link and not e.errno == errno.EEXIST:
                            raise FSQReenqueueError(e.errno, wrap_io_os_err(e))
                    finally:
                        os.unlink(tmp_name)
            finally:
                for tmp_fo in tmp_fos:
                    tmp_fo.close()
        return item_id
    except Exception, e:
        try:
            if link:
                tmp_name = os.path.join(fsq_path.tmp(src_queue, item_id))
                try:
                    os.unlink(tmp_name)
                except (OSError, IOError, ), err:
                    if err.errno == errno.ENOENT:
                        pass
                raise FSQReenqueueError(err.errno, wrap_io_os_err(err))
            else:
                for tmp_name in tmp_names:
                    try:
                        os.unlink(tmp_name)
                    except (OSError, IOError, ), err:
                        if err.errno == errno.ENOENT:
                            pass
                        raise FSQReenqueueError(err.errno, wrap_io_os_err(err))
        except (OSError, IOError, ), err:
            if err.errno != errno.ENOENT:
               raise FSQReenqueueError(err.errno, wrap_io_os_err(err))
        except OSError, err:
            if err.errno != errno.ENOENT:
               raise FSQReenqueueError(err.errno, wrap_io_os_err(err))
        if (isinstance(e, OSError) or isinstance(e, IOError)) and\
                not isinstance(e, FSQError):
            raise FSQReenqueueError(e.errno, wrap_io_os_err(e))
        raise e
    finally:
        if not link:
            src_file.close()

def sreenqueue(item_id, item_s, *args, **kwargs):
    '''Enqueue a string, or string-like object to other queues, with arbitrary
       arguments, sreenqueue is to reenqueue what sprintf is to printf,
       sreenqueue is to vsreenqueue what sprintf is to vsprintf.
    '''
    return vsreenqueue(item_id, item_s, args, **kwargs)

def vsreenqueue(item_id, item_s, args, **kwargs):
    '''Enqueue a string, or string-like object to other queues, with arbitrary
       arguments, sreenqueue is to reenqueue what sprintf is to printf,
       sreenqueue is to vsreenqueue what sprintf is to vsprintf.
    '''
    charset = kwargs.get('charset', _c.FSQ_CHARSET)
    if kwargs.has_key('charset'):
        del kwargs['charset']

    kwargs['item_id'] = item_id
    # we coerce here because StringIO.StringIO will coerce on file-write,
    # and cStringIO.StringIO has a bug which injects NULs for unicode
    if isinstance(item_s, unicode):
        try:
            item_s = item_s.encode(charset)
        except UnicodeEncodeError:
            raise FSQCoerceError(errno.EINVAL, u'cannot encode item with'\
                                 u' charset {0}'.format(charset))

    return vreenqueue(StringIO(item_s), item_id, args, **kwargs)
