__version__ = "0.1"

from tls.c import api

if __name__ == '__main__':
    version = api.version_info()
    template = 'OpenTLS {major}.{minor}.{fix}{patch} ({status})'
    print(template.format(**version._asdict()))
