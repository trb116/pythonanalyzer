"""Python API for accessing OpenSSL BIO objects"""
from __future__ import absolute_import, division, print_function
import functools
import io
import sys

from tls.c import api
from tls import err

try:
    from io import SEEK_SET, SEEK_CUR, SEEK_END
except ImportError:
    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2


class BIOChain(object):
    """Implements an io.IOBase interface for OpenSSL BIO chains.

    BIOChain instances can be used as file like objects in Python.
    """

    def _not_closed(method):

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.closed():
                return method(self, *args, **kwargs)
            raise IOError('already closed')
        return wrapper

    def __init__(self, bio, bufsize=1024):
        self._bio = bio
        self._bufsize = bufsize

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getitem__(self, pos):
        if pos < 0:
            raise IndexError("list index out of range")
        bio = self.c_bio
        while pos > 0:
            nxt = api.BIO_next(bio)
            if api.cast('void*', nxt) == api.NULL:
                raise IndexError("list index out of range")
            bio = nxt
            pos -= 1
        return bio

    def pop(self):
        bio = self._bio
        nxt = api.BIO_pop(bio)
        if api.cast('void*', nxt) != api.NULL:
            self._bio = nxt
        return bio

    def push(self, bio):
        self._bio = api.BIO_push(bio, self._bio)

    @property
    def bio_types(self):
        types = []
        bio = self._bio
        while api.cast('void*', bio) != api.NULL:
            types.insert(0, api.BIO_method_type(bio))
            bio = api.BIO_next(bio)
        return types

    @property
    def c_bio(self):
        return self._bio

    # io.IOBase

    @err.log_errors
    def close(self):
        if self._bio is not api.NULL:
            api.BIO_free_all(self._bio)
        self._bio = api.NULL

    def closed(self):
        return self._bio is api.NULL

    def fileno(self):
        raise IOError('unsupported operation')

    @_not_closed
    @err.log_errors
    def flush(self):
        api.BIO_flush(self._bio)

    def isatty(self):
        raise IOError('unsupported operation')

    @_not_closed
    def readable(self):
        return True

    @_not_closed
    @err.log_errors
    def readline(self, limit=-1):
        limit = sys.maxsize if limit < 0 else limit
        segments = []
        while limit > 0:
            size = api.BIO_pending(self._bio)
            buf = api.new('char[]', min(limit, size if size > 1 else self._bufsize))
            read = api.BIO_gets(self._bio, buf, len(buf))
            if read <= 0 and not api.BIO_should_retry(self._bio):
                raise IOError('unsupported operation')
            segments.append(api.buffer(buf, read)[:])
            limit -= read
            if segments[-1][-1:] == b'\n':
                break
        return b''.join(segments)

    @_not_closed
    @err.log_errors
    def readlines(self, hint=-1):
        hint = sys.maxsize if hint < 0 else hint
        lines = []
        while hint > 0:
            try:
                line = self.readline()
                lines.append(line)
                hint -= len(line)
            except IOError:
                if len(lines) == 0:
                    raise
                break
        return lines

    @_not_closed
    @err.log_errors
    def seek(self, offset, whence=SEEK_SET):
        if whence != SEEK_SET:
            raise IOError('unsupported operation')
        rval = api.BIO_seek(self._bio, offset)
        if rval < 0:
            raise IOError('unsupported operation')
        return offset

    @_not_closed
    def seekable(self):
        return True

    @_not_closed
    @err.log_errors
    def tell(self):
        return api.BIO_tell(self._bio)

    def truncate(self):
        raise IOError('unsupported operation')

    @_not_closed
    def writable(self):
        return True

    @_not_closed
    @err.log_errors
    def writelines(self, lines):
        for line in lines:
            data = api.new('char[]', line)
            offset = 0
            while offset < len(line):
                ptr = data + offset
                size = len(line) - offset
                written = api.BIO_write(self._bio, ptr, size)
                if written <= 0 and not api.BIO_should_retry(self._bio):
                    raise IOError('unsupported operation')
                offset += written

    # io.RawIOBase

    @_not_closed
    @err.log_errors
    def read(self, n=-1):
        if n < 0:
            return self.readall()
        data = api.new('char[]', n)
        read = api.BIO_read(self._bio, data, len(data))
        if read < 0:
            raise IOError('unsupported operation')
        return api.string(data)

    @_not_closed
    @err.log_errors
    def readall(self):
        segments = []
        while True:
            size = api.BIO_pending(self._bio)
            data = api.new('char[]', size if size > 1 else self._bufsize)
            read = api.BIO_read(self._bio, data, len(data))
            if read < 0:
                raise IOError('unsupported operation')
            if read == 0:
                break
            segments.append(api.buffer(data, read)[:])
        return b"".join(segments)

    def readinto(self, b):
        raise IOError('unsupported operation')

    @_not_closed
    @err.log_errors
    def write(self, b):
        data = api.new('char[]', b)
        writen = api.BIO_write(self._bio, data, len(data))
        if writen <= 0 and not api.BIO_should_retry(self._bio):
            raise IOError('unsupported operation')
        return writen


io.RawIOBase.register(BIOChain)
