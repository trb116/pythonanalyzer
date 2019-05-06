from setuptools import setup, find_packages

version = '0.1'

setup(
    name='shadowsocks-gtk',
    version=version,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    author='apporc',
    author_email='apporc@gmail.com',
    url='https://github.com/apporc/shadowsocks-gtk',
    license='http://opensource.org/licenses/MIT',
    description='ShadowSocks Gtk Client',
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications',
        'Environment :: X11 Applications :: Gnome',
        'Environment :: X11 Applications :: GTK',
        'Framework :: Twisted',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        ],
    entry_points={
        'console_scripts': [
            'sslocal = shadowsocks_gtk.local:main',
        ],
        'gui_scripts': [
            'shadowsocks-gtk = shadowsocks_gtk.shadowsocks:main',
        ]
    }
)
