# -*- coding: utf-8 -*-


class BaseConfig(object):
    import os

    PROJECT = "aurora"

    app_folder = os.path.abspath(os.path.dirname(__file__))
    template_folder = os.path.join(app_folder, 'templates')
    static_folder = os.path.join(app_folder, 'static')

    DEBUG = False
    TESTING = False

    CSRF_ENABLED = True
    # http://flask.pocoo.org/docs/quickstart/#sessions
    SECRET_KEY = 'aurora-secret-key'

    # sqlalchemy settings
    # sqlite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///aurora.db'
    # postgresql
    #SQLALCHEMY_DATABASE_URI = 'postgresql://aurora:aurora@localhost:5432/' + \
    #    'auroradb'

    # Aurora paths
    AURORA_PATH = os.path.join(os.path.expanduser('~'), '.aurora')
    AURORA_SETTINGS = os.path.join(AURORA_PATH, 'settings.py')
    AURORA_PROJECTS_PATH = os.path.join(AURORA_PATH, 'projects')
    AURORA_TMP_PATH = '/tmp/aurora'
    AURORA_TMP_DEPLOYMENTS_PATH = os.path.join(AURORA_TMP_PATH, 'deployments')
    LOG_FOLDER = os.path.join(AURORA_PATH, 'logs')

    # Debug toolbar settings
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class TestConfig(BaseConfig):
    TESTING = True
    CSRF_ENABLED = False

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
