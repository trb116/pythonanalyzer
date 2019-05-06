"""Test SSL methods"""
from __future__ import absolute_import, division, print_function

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tls.c import api


class TestSSLMethod(unittest.TestCase):

    @unittest.skipIf(api.OPENTLS_NO_SSL2, 'deprecated in openssl 1.0.0')
    def test_ssl_v2(self):
        """
        api.SSLv2_method returns the SSLv2 protocol method if SSLv2 is
        available in the underlying OpenSSL library.
        """
        self.assertTrue(api.SSLv2_method())

    @unittest.skipIf(not api.OPENTLS_NO_SSL2, 'deprecated in openssl 1.0.0')
    def test_ssl_v2_disabled(self):
        """
        api.SSLv2_method raises NotImplementedError if SSLv2 is available in
        the underlying OpenSSL library.
        """
        with self.assertRaises(NotImplementedError):
            api.SSLv2_method()

    @unittest.skipIf(api.OPENTLS_NO_SSL2, 'deprecated in openssl 1.0.0')
    def test_ssl_v2_client(self):
        """
        api.SSLv2_client_method returns the SSLv2 protocol method if SSLv2 is
        available in the underlying OpenSSL library.
        """
        self.assertTrue(api.SSLv2_client_method())

    @unittest.skipIf(not api.OPENTLS_NO_SSL2, 'deprecated in openssl 1.0.0')
    def test_ssl_v2_client_disabled(self):
        """
        api.SSLv2_client_method raises NotImplementedError if SSLv2 is
        available in the underlying OpenSSL library.
        """
        with self.assertRaises(NotImplementedError):
            api.SSLv2_client_method()

    @unittest.skipIf(api.OPENTLS_NO_SSL2, 'deprecated in openssl 1.0.0')
    def test_ssl_v2_server(self):
        """
        api.SSLv2_server_method returns the SSLv2 protocol method if SSLv2 is
        available in the underlying OpenSSL library.
        """
        self.assertTrue(api.SSLv2_server_method())

    @unittest.skipIf(not api.OPENTLS_NO_SSL2, 'deprecated in openssl 1.0.0')
    def test_ssl_v2_server_disabled(self):
        """
        api.SSLv2_server_method raises NotImplementedError if SSLv2 is
        available in the underlying OpenSSL library.
        """
        with self.assertRaises(NotImplementedError):
            api.SSLv2_server_method()

    def test_ssl_v3(self):
        self.assertTrue(api.SSLv3_method())

    def test_ssl_v3_client(self):
        self.assertTrue(api.SSLv3_client_method())

    def test_ssl_v3_server(self):
        self.assertTrue(api.SSLv3_server_method())

    def test_tls_v1(self):
        self.assertTrue(api.TLSv1_method())

    def test_tls_v1_client(self):
        self.assertTrue(api.TLSv1_client_method())

    def test_tls_v1_server(self):
        self.assertTrue(api.TLSv1_server_method())

    def test_ssl_v23(self):
        self.assertTrue(api.SSLv23_method())

    def test_ssl_v23_client(self):
        self.assertTrue(api.SSLv23_client_method())

    def test_ssl_v23_server(self):
        self.assertTrue(api.SSLv23_server_method())
