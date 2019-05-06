import os
import shutil
import errno
import sys
import unittest

from . import constants as _test_c
from .. import constants as _c
from .internal import normalize

class FSQTestCase(unittest.TestCase):
    def setUp(self):
        _test_c.COUNT = 0
        try:
            shutil.rmtree(_test_c.TEST_DIR)
        except (OSError, IOError, ), e:
            if e.errno != errno.ENOENT:
                raise e
        os.mkdir(_test_c.TEST_DIR, 00750)
        os.mkdir(_test_c.ROOT1, 00750)
        os.mkdir(_test_c.ROOT2, 00750)
        _c.FSQ_ROOT = _test_c.ROOT1
        normalize()

    def tearDown(self):
        _c.FSQ_ROOT = _test_c.ORIG_ROOT
        try:
            shutil.rmtree(_test_c.TEST_DIR)
        except(OSError, IOError, ), e:
            if e.errno != errno.ENOENT:
                raise e
        sys.stderr.write('Total Tests Run: {0} ... '.format(_test_c.COUNT))
        _test_c.TOTAL_COUNT += _test_c.COUNT
        normalize()
