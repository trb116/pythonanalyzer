from flask.ext.script import Manager, Server
from flask.ext.alembic import ManageMigrations

from aurora_app import create_app
from .extensions import db


def create_manager(app):
    manager = Manager(app)
    manager.add_option('-c', '--config',
                       dest="config",
                       required=False,
                       help="config file")

    manager.add_command("runserver", Server())
    manager.add_command("migrate", ManageMigrations(
        config_path='aurora_app/migrations/alembic.ini'))

    def create_superuser_dialog():
        import getpass
        from email.utils import parseaddr

        print "You need to create a superuser!"

        username = raw_input('Username [{0}]: '.format(getpass.getuser()))
        if not username:
            username = getpass.getuser()

        email = None
        while not email:
            email = parseaddr(raw_input('Email: '))[1]

        passwords = lambda: (getpass.getpass(),
                             getpass.getpass('Password (retype): '))

        password, retyped_password = passwords()

        while password == '' or password != retyped_password:
            print 'Passwords do not match or your password is empty!'
            password, retyped_password = passwords()

        return username, email, password

    @manager.command
    def init_config():
        """Creates settings.py in default folder."""
        import inspect
        from .config import BaseConfig
        lines = inspect.getsource(BaseConfig).split('\n')[1:]
        lines = [line[4:] for line in lines]
        open(BaseConfig.AURORA_SETTINGS, 'w').write('\n'.join(lines))
        print 'Configuration was written at: ' + BaseConfig.AURORA_SETTINGS

    @manager.command
    def init_db():
        """Creates aurora database."""
        from .users.models import User
        from .users.constants import ROLES

        db.create_all()

        username, email, password = create_superuser_dialog()

        superuser = User(username=username, password=password, email=email,
                         role=ROLES['ADMIN'])
        db.session.add(superuser)
        db.session.commit()

    return manager


def main():
    import os
    import sys

    if not os.path.exists('aurora.db') and not 'init_db' in sys.argv:
        print 'You need to run "init_db" at first.'
        return

    manager = create_manager(create_app)
    manager.run()

if __name__ == "__main__":
    main()
