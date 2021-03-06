import os
import sys
import re

from setuptools import setup
from setuptools.command.test import test as TestCommand

py_version = sys.version_info[:2]

here = os.path.abspath(os.path.dirname(__file__))


def get_version(package):
    """Return package version as listed in `__version__` in `init.py`"""
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

PROJECT_NAME = "django-testclient-extensions"
PROJECT_URL = "https://github.com/ikame/django-test-client-extensions"
PROJECT_VERSION = get_version("testclient_extensions")
PROJECT_DESCRIPTION = "Extensions to Django's built-in test client."

AUTHOR = "ikame"
AUTHOR_EMAIL = "anler86@gmail.com"

try:
    README = open(os.path.join(here, "README.rst")).read()
    README += open(os.path.join(here, "HISTORY.rst")).read()
except IOError:
    README = PROJECT_URL


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(name=PROJECT_NAME,
      version=PROJECT_VERSION,
      description=PROJECT_DESCRIPTION,
      long_description=README,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=PROJECT_URL,
      license="MIT",
      packages=["testclient_extensions"],
      install_requires=["six", "mock"],
      tests_require=["pytest", "mock"],
      cmdclass={"test": PyTest},
      keywords="django test client development dev tools utilities",
      classifiers=[
          "Environment :: Plugins",
          "Environment :: Console",
          "Environment :: Web Environment",
          "Intended Audience :: Developers",
          "Intended Audience :: Financial and Insurance Industry",
          "Framework :: Django",
          "Topic :: Database :: Front-Ends",
          "Topic :: Documentation",
          "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
          "Topic :: Internet :: WWW/HTTP :: Site Management",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Topic :: Software Development :: Libraries :: Python Modules"])
