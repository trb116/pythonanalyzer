"""Test OpenSSL error handling"""
from __future__ import absolute_import, division, print_function

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tls.c import api


class TestErrorFetch(unittest.TestCase):

    first = 0x2006D080
    last = 0x140943E8

    def setUp(self):
        while api.ERR_get_error() != 0:
            pass
        api.ERR_put_error(0x20, 0x6D, 0x80, api.NULL, 0)
        api.ERR_put_error(0x14, 0x94, 0x3E8, api.NULL, 0)

    def tearDown(self):
        self.count_errors_on_stack()

    def count_errors_on_stack(self):
        count = 0
        while api.ERR_get_error() != 0:
            count += 1
        return count

    def test_error_get(self):
        self.assertEqual(api.ERR_get_error(), self.first)
        self.assertEqual(api.ERR_get_error(), self.last)
        self.assertEqual(self.count_errors_on_stack(), 0)

    def test_error_peek(self):
        self.assertEqual(api.ERR_peek_error(), self.first)
        self.assertEqual(self.count_errors_on_stack(), 2)

    def test_error_peek_last(self):
        self.assertEqual(api.ERR_peek_last_error(), self.last)
        self.assertEqual(self.count_errors_on_stack(), 2)


class TestErrorParse(unittest.TestCase):

    code = 0x2006D080
    text = b'error:2006D080:BIO routines:BIO_new_file:no such file'

    def test_error_string(self):
        value = api.ERR_error_string(self.code, api.NULL)
        self.assertEqual(api.string(value), self.text)

    def test_error_string_n(self):
        stop = len(self.text) - 1
        buf = api.new('char[]', 2 * len(self.text))
        api.ERR_error_string_n(self.code, buf, stop)
        self.assertEqual(api.string(buf), self.text[:stop - 1])

    def test_lib_error_string(self):
        value = api.ERR_lib_error_string(self.code)
        self.assertEqual(api.string(value), self.text.split(b':')[2])

    def test_func_error_string(self):
        value = api.ERR_func_error_string(self.code)
        self.assertEqual(api.string(value), self.text.split(b':')[3])

    def test_reason_error_string(self):
        value = api.ERR_reason_error_string(self.code)
        self.assertEqual(api.string(value), self.text.split(b':')[4])

    def test_code_pack(self):
        code = api.ERR_PACK(0x20, 0x6D, 0x80)
        self.assertEqual(code, self.code)

    def test_code_get_lib(self):
        code = api.ERR_GET_LIB(self.code)
        self.assertEqual(code, 0x20)

    def test_code_get_func(self):
        code = api.ERR_GET_FUNC(self.code)
        self.assertEqual(code, 0x6D)

    def test_code_get_reason(self):
        code = api.ERR_GET_REASON(self.code)
        self.assertEqual(code, 0x80)

    def test_load_strings(self):
        lib = api.ERR_get_next_error_library()
        func = 1
        reason = 1
        code = api.ERR_PACK(lib, func, reason)
        array = api.new('ERR_STRING_DATA[2]')
        array[0].error = code
        array[0].string = api.new('char[]', b"MY ERROR")
        array[0].error = 0
        array[0].string = api.NULL
        api.ERR_load_strings(lib, array)
