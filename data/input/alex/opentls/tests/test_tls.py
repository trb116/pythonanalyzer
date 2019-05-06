from __future__ import absolute_import, division, print_function
import doctest

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import tls

PEP386 = r"""^(?P<version>\d+\.\d+)(?P<extraversion>(?:\.\d+)*)(?:(?P<prerel>[abc]|rc)(?P<prerelversion>\d+(?:\.\d+)*))?(?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?$"""


class TestTls(unittest.TestCase):

    def test_valid_version(self):
        if hasattr(self, 'assertRegex'):
            self.assertRegex(tls.__version__, PEP386)
        else:
            self.assertRegexpMatches(tls.__version__, PEP386)

    def test_readme(self):
        doctest.testfile('../README.rst')
