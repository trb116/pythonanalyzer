"""Wrapper for Python objects for OpenSSL BIO system"""
from __future__ import absolute_import, division, print_function
from tls.c import api
from tls.io import BIOBase


class BIOMethod(BIOBase):
    """Presents an OpenSSL BIO method for a file like object.

    The new BIO method is available as the method attribute on class instances.
    The original object is the fileobj attribute. To create automatically have
    a BIO object created with the associated method retained until the BIO
    object is garbage collected, use the wrap_io class method.
    """

    @classmethod
    def wrap_io(cls, fileobj):
        """Create a new BIO object for a file like Python object.

        Returns the cffi.Cdata instance for BIO pointer. The associated method
        object will be retained until the cffi.Cdata is deleted. The caller is
        required to call api.BIO_free on the pointer to release memory
        allocated by OpenSSL.
        """
        wrapper = cls(fileobj)
        bio = api.new('BIO*')
        api.BIO_set(bio, wrapper.method)
        return bio

    def __init__(self, fileobj):
        method = api.new('BIO_METHOD*')
        method.type = api.BIO_TYPE_SOURCE_SINK | 0xFF
        method.name = self._name = api.new('char[]', repr(fileobj).encode())
        method.bwrite = self._bwrite = api.callback('int (*)(BIO*, const char*, int)',
                self.write)
        method.bread = self._bread = api.callback('int (*)(BIO*, char*, int)',
                self.read)
        method.bputs = self._bputs = api.callback('int (*)(BIO*, const char*)',
                self.puts)
        method.bgets = self._bgets = api.callback('int (*)(BIO*, char*, int)',
                self.gets)
        method.ctrl = self._ctrl = api.callback('long (*)(BIO*, int, long, void*)',
                self.ctrl)
        method.create = self._create = api.callback('int (*)(BIO*)',
                self.create)
        method.destroy = api.NULL
        method.callback_ctrl = api.NULL
        self.method = method
        self.fileobj = fileobj

    def create(self, bio):
        bio.init = 1
        bio.num = 0
        bio.ptr = api.NULL
        return 1

    def write(self, bio, data, length):
        try:
            self.fileobj.write(api.buffer(data, length))
            return length
        except:
            return self.BIO_ERROR

    def read(self, bio, data, length):
        try:
            buff = api.buffer(data, length)
            if hasattr(self.fileobj, 'readinto'):
                count = self.fileobj.readinto(buff)
                count = count if count is not None else 0
            else:
                tmp = self.fileobj.read(length)
                count = len(tmp)
                buff[:count] = tmp
            return count
        except:
            return self.BIO_ERROR

    def ctrl_flush(self, bio, cmd, num, obj):
        self.fileobj.flush()
        return 1

    def ctrl_reset(self, bio, cmd, num, obj):
        self.fileobj.seek(0)
        return 0

    def ctrl_seek(self, bio, cmd, num, obj):
        return self.fileobj.seek(num)

    def ctrl_tell(self, bio, cmd, num, obj):
        return self.fileobj.tell()
