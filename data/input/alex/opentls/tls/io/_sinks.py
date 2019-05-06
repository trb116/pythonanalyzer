"""Types specialisations of BIOChain"""
from __future__ import absolute_import, division, print_function
from tls.io import BIOChain
from tls.c import api
from tls import err


class BIOFile(BIOChain):
    """Specialise BIOChain for file BIOs.

    Files may be opened in one of the following modes:

     'r'  Open for reading.
          The stream is positioned at the beginning of the file.
     'r+' Open for reading and writing.
          The stream is positioned at the beginning of the file.
     'w'  Truncate to zero length or create text file for writing.
          The stream is positioned at the beginning of the file.
     'w+' Open for reading and writing.
          The stream is positioned at the beginning of the file.
     'a'  Open for writing. The file is created if it does not exist.
          The stream is positioned at the end of the file.
     'a+' Open for reading and writing.
          The stream is positioned at the end of the file.

    If the mode is not recognised ValueError will be raised. IOError will be
    raised if there was an issue opening the file.
    """

    MODES = set(['r', 'r+', 'w', 'w+', 'a', 'a+'])

    def __init__(self, filename, mode='r'):
        if mode not in self.MODES:
            msg = "mode string must begin with one of "
            msg += " ".join("'{0}'".format(m) for m in sorted(self.MODES))
            msg += " not '{0}'".format(mode)
            raise ValueError(msg)
        self._filename = filename.encode()
        self._mode = mode.encode()
        mode = api.new('char[]', self._mode)
        filename = api.new('char[]', self._filename)
        bio = api.BIO_new_file(filename, mode)
        if api.cast('void*', bio) == api.NULL:
            messages = err.log_errors()
            raise IOError(messages[0])
        super(BIOFile, self).__init__(bio)

    def readable(self):
        return self._mode.startswith(b'r') or self._mode.endswith(b'+')

    def writable(self):
        return self._mode.startswith(b'w') or self._mode.endswith(b'+')


class BIOMemBuffer(BIOChain):
    """Specialises BIOChain for BIO memory buffers.

    If an initial value is passed the BIO will be read only.
    """

    def __init__(self, initial_value=None):
        if initial_value is not None:
            self._buffer = api.new('char[]', initial_value)
            bio = api.BIO_new_mem_buf(self._buffer, len(initial_value))
        else:
            bio = api.BIO_new(api.BIO_s_mem())
        super(BIOMemBuffer, self).__init__(bio)

    def writable(self):
        return not hasattr(self, '_buffer')


class BIONull(BIOChain):
    """Specialise BIOChain for NULL sinks and sources."""

    def __init__(self):
        bio = api.BIO_new(api.BIO_s_null())
        super(BIONull, self).__init__(bio)
