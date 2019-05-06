try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import re


with open('README.rst') as src:
  long_description = src.read()


def version(filename='aboutyou/api.py'):
    version_re = re.compile(r'VERSION = ["\']([^"\']*)["\']')
    with open(filename) as f:
        for line in f:
            version = version_re.match(line)
            if version is not None:
                return version.group(1)
    raise ValueError('version not found')


setup(
    name='aboutyou',
    packages=['aboutyou', 'aboutyou.django'],
    version=version(),
    install_requires=['pylibmc>=1.3.0', 'PyYAML'],
    description='A connection to the aboutyou.de shop.',
    long_description=long_description,
    author='Arne Simon',
    author_email='arne.simon@slice-dice.de',
    license='MIT',
    url='https://bitbucket.org/slicedice/aboutyou-shop-sdk-python/overview',
    download_url='https://bitbucket.org/slicedice/aboutyou-shop-sdk-python/downloads',
    keywords=['aboutyou', 'shop', 'collins', 'api'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet',
        'Topic :: Office/Business',
    ]
)
