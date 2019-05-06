import os

from flask import Flask, render_template, url_for, g, request, redirect

# Config
from .config import BaseConfig

# Utils
from .utils import make_dir

# Extensions
from .extensions import db, login_manager, debugtoolbar, gravatar

# Models
from .users.models import User
from .projects.models import Project
from .tasks.models import Task
from .deployments.models import Deployment

# Blueprints
from .users.views import users
from .projects.views import projects
from .stages.views import stages
from .tasks.views import tasks
from .notifications.views import notifications
from .frontend.views import frontend
from .deployments.views import deployments

__all__ = ['create_app']

DEFAULT_BLUEPRINTS = [
    frontend,
    projects,
    stages,
    tasks,
    notifications,
    deployments,
    users,
]


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = BaseConfig.PROJECT
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name, instance_relative_config=True)

    configure_app(app, config)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_hook(app)
    configure_logging(app)
    configure_context_processors(app)
    configure_error_handlers(app)

    return app


def configure_app(app, config=None):
    # Default configuration
    app.config.from_object(BaseConfig)

    app.template_folder = BaseConfig.template_folder
    app.static_folder = BaseConfig.static_folder

    if config:
        if isinstance(config, basestring):
            app.config.from_pyfile(config)
        else:
            app.config.from_object(config)
    elif os.path.exists(BaseConfig.AURORA_SETTINGS):
        app.config.from_pyfile(BaseConfig.AURORA_SETTINGS)

    app.template_folder = BaseConfig.template_folder
    app.static_folder = BaseConfig.static_folder

    # Make dirs
    make_dir(app.config['AURORA_PATH'])
    make_dir(app.config['AURORA_PROJECTS_PATH'])
    make_dir(app.config['AURORA_TMP_PATH'])
    make_dir(app.config['AURORA_TMP_DEPLOYMENTS_PATH'])
    make_dir(app.config['LOG_FOLDER'])


def configure_hook(app):
    from flask.ext.login import current_user

    @app.before_request
    def check_login():
        g.user = current_user if current_user.is_authenticated() else None

        if (request.endpoint and request.endpoint != 'static' and
           (not getattr(app.view_functions[request.endpoint],
            'is_public', False)
           and g.user is None)):
            return redirect(url_for('frontend.login', next=request.path))


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_extensions(app):
    # flask-sqlalchemy
    db.init_app(app)

    # flask-login
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    login_manager.init_app(app)

    # flask-debugtoolbar
    debugtoolbar(app)

    # flask-gravatar
    gravatar.init_app(app)


def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    if app.debug or app.testing:
        # Skip debug and test mode. Just check standard output.
        return

    import logging.handlers
    # Set info level on logger, which might be overwritten by handlers.
    # Suppress DEBUG messages.
    app.logger.setLevel(logging.INFO)

    info_log = os.path.join(app.config['LOG_FOLDER'], 'info.log')
    info_file_handler = logging.handlers.RotatingFileHandler(
        info_log, maxBytes=100000, backupCount=10)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(info_file_handler)


def configure_context_processors(app):
    """Configure contest processors."""

    @app.context_processor
    def projects():
        """Returns all projects."""
        return {'projects': Project.query.all()}

    @app.context_processor
    def version():
        from . import __version__
        return {'AURORA_VERSION': __version__}

    @app.context_processor
    def recent_deployments():
        def get_recent_deploments(object):
            if object.__tablename__ == 'projects':
                stages_ids = [stage.id for stage in object.stages]
                result = Deployment.query.filter(
                    Deployment.stage_id.in_(stages_ids))
            if object.__tablename__ == 'stages':
                result = Deployment.query.filter_by(stage_id=object.id)
            if object.__tablename__ == 'tasks':
                result = Deployment.query.filter(
                    Deployment.tasks.any(Task.id.in_([object.id])))
            if object.__tablename__ == 'users':
                result = Deployment.query.filter_by(user_id=object.id)
            return result.order_by('started_at desc').limit(3).all()
        return dict(get_recent_deployments=get_recent_deploments)

    # # To exclude caching of static
    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)

    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.static_folder, filename)
                values['q'] = int(os.stat(file_path).st_mtime)
        return url_for(endpoint, **values)


def configure_error_handlers(app):

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/page_not_found.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/server_error.html"), 500
