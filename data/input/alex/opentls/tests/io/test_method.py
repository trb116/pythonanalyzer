"""Test Python IO API for OpenSSL BIO"""
from __future__ import absolute_import, division, print_function

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from ..c.test_bio_sink import BioWrite, BioRead
from tls.c import api
from tls import io


class TestStringIOWrite(BioWrite, unittest.TestCase):

    def setUp(self):
        fileobj = BytesIO()
        self.bio = io.wrap_io(fileobj)

    test_eof = unittest.expectedFailure(BioWrite.test_eof)
    test_puts = unittest.expectedFailure(BioWrite.test_puts)


class TestStringIORead(BioRead, unittest.TestCase):

    def setUp(self):
        fileobj = BytesIO(api.string(self.data))
        self.bio = io.wrap_io(fileobj)

    test_ctrl_pending = unittest.expectedFailure(BioRead.test_ctrl_pending)
    test_eof = unittest.expectedFailure(BioRead.test_eof)
    test_gets = unittest.expectedFailure(BioRead.test_gets)
    test_pending = unittest.expectedFailure(BioRead.test_pending)
