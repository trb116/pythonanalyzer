from setuptools import setup, find_packages


setup(
    name='pyunite',
    version='0.1',
    description='Python API for Unite.vim',
    # Author details
    author='Alejandro Hernandez',
    author_email='alejandro@coinapex.com',
    license='MIT',
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['.git', 'dist', 'contrib', 'docs']),
    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    # install_requires=['pytest', 'funcy', 'pathlib', 'wrapt'],
)
