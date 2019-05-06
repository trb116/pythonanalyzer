"""Test specialisation of tls.io.BIOChain"""
from __future__ import absolute_import, division, print_function
import os
import tempfile
import mock

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tls.c import api
from tls import io

from .test_chain import ChainTest, TestChainRead, TestChainWrite


class TestFileRead(TestChainRead):

    @classmethod
    def setUpClass(cls):
        fd, cls.filename = tempfile.mkstemp()
        os.close(fd)
        with open(cls.filename, 'wb') as dest:
            dest.write(cls.DATA)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.filename)

    def setUp(self):
        self.fileobj = io.BIOFile(self.filename, 'r')
        self.filter = api.BIO_new(api.BIO_f_null())
        self.sink = self.fileobj.c_bio
        self.fileobj.push(self.filter)
        self.bio = self.fileobj.c_bio

    def test_readable(self):
        self.assertTrue(self.fileobj.readable())

    def test_writable(self):
        self.assertFalse(self.fileobj.writable())


class TestFileWrite(TestChainWrite):

    @classmethod
    def setUpClass(cls):
        fd, cls.filename = tempfile.mkstemp()
        os.close(fd)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.filename)

    def setUp(self):
        self.fileobj = io.BIOFile(self.filename, 'w')
        self.filter = api.BIO_new(api.BIO_f_null())
        self.sink = self.fileobj.c_bio
        self.fileobj.push(self.filter)
        self.bio = self.fileobj.c_bio

    def test_readable(self):
        self.assertFalse(self.fileobj.readable())

    def test_writable(self):
        self.assertTrue(self.fileobj.writable())


class TestFileBio(unittest.TestCase):

    @mock.patch('tls.err.logger')
    def test_invalid_filename(self, _):
        self.assertRaises(IOError, io.BIOFile, '_not_a_file', 'r')

    def test_invalid_mode(self):
        self.assertRaises(ValueError, io.BIOFile, '', 'x')


class TestMemBufferWrite(TestChainWrite):

    def setUp(self):
        self.fileobj = io.BIOMemBuffer()
        self.filter = api.BIO_new(api.BIO_f_null())
        self.sink = self.fileobj.c_bio
        self.fileobj.push(self.filter)
        self.bio = self.fileobj.c_bio


class TestMemBufferRead(TestChainRead):

    def setUp(self):
        self.fileobj = io.BIOMemBuffer(self.DATA)
        self.filter = api.BIO_new(api.BIO_f_null())
        self.sink = self.fileobj.c_bio
        self.fileobj.push(self.filter)
        self.bio = self.fileobj.c_bio

    def test_writable(self):
        self.assertFalse(self.fileobj.writable())


class TestNullBio(ChainTest, unittest.TestCase):

    def setUp(self):
        self.fileobj = io.BIONull()
        self.filter = api.BIO_new(api.BIO_f_null())
        self.sink = self.fileobj.c_bio
        self.fileobj.push(self.filter)
        self.bio = self.fileobj.c_bio

    def tearDown(self):
        if self.fileobj.c_bio is not api.NULL:
            api.BIO_free_all(self.bio)
