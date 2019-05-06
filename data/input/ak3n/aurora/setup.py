from setuptools import setup, find_packages
from setuptools.command import install

import aurora_app

install_requires = [
    'Fabric==1.6.0',
    'Flask==0.10.1',
    'Flask-Alembic==0.1',
    'Flask-Gravatar==0.3.0',
    'Flask-Login==0.2.6',
    'Flask-SQLAlchemy==0.16',
    'Flask-Script==0.5.3',
    'Flask-WTF==0.8.3',
    'GitPython==0.3.2.RC1',
    'alembic==0.6.0',
    'psycopg2==2.5',
    'Flask-DebugToolbar',
]


class install_with_submodules(install.install):

    def run(self):
        import os
        if os.path.exists('.git'):
            os.system('git submodule init')
            os.system('git submodule update')
        install.install.run(self)

setup(
    name='Aurora',
    version=aurora_app.__version__,
    author='Eugene Akentyev',
    author_email='ak3ntev@gmail.com',
    url='https://github.com/ak3n/aurora',
    description='A web interface for Fabric',
    long_description=open('README.rst').read(),
    cmdclass={"install": install_with_submodules},
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    license='MIT',
    entry_points={
        'console_scripts': [
            'aurora = aurora_app.runner:main',
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
    ],
    dependency_links=['https://github.com/ak3n/flask-alembic/' +
                      'tarball/master#egg=flask-alembic-0.1']
)
