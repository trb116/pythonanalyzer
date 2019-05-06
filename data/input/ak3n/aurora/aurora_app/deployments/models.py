import time
import os
from datetime import datetime

from flask import url_for, current_app

from ..extensions import db
from ..tasks.models import Task

from .constants import STATUSES, BOOTSTRAP_ALERTS


deployments_tasks_table = db.Table('deployments_tasks', db.Model.metadata,
                                   db.Column('deployment_id', db.Integer,
                                             db.ForeignKey('deployments.id')),
                                   db.Column('task_id', db.Integer,
                                             db.ForeignKey('tasks.id')))


class Deployment(db.Model):
    __tablename__ = "deployments"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.SmallInteger, default=STATUSES['READY'])
    branch = db.Column(db.String(32), default='master')
    commit = db.Column(db.String(128))
    started_at = db.Column(db.DateTime(), default=datetime.now)
    finished_at = db.Column(db.DateTime())
    code = db.Column(db.Text())
    log = db.Column(db.Text())
    # Relations
    stage_id = db.Column(db.Integer(),
                         db.ForeignKey('stages.id'), nullable=False)
    user_id = db.Column(db.Integer(),
                        db.ForeignKey('users.id'), nullable=False)
    tasks = db.relationship(Task,
                            secondary=deployments_tasks_table,
                            backref="deployments")

    def get_tmp_path(self):
        return os.path.join(current_app.config['AURORA_TMP_DEPLOYMENTS_PATH'],
                            '{0}'.format(self.id))

    def bootstrap_status(self):
        return BOOTSTRAP_ALERTS[self.status]

    def show_status(self):
        for status, number in STATUSES.iteritems():
            if number == self.status:
                return status

    def is_running(self):
        return self.status == STATUSES['RUNNING']

    def show_tasks_list(self):
        template = '<a href="{0}">{1}</a>'
        return ', '.join([template.format(url_for('tasks.view', id=task.id),
                                          task.name) for task in self.tasks])

    def get_log_path(self):
        return os.path.join(self.get_tmp_path(), 'log')

    def get_log_lines(self):
        if self.log:
            return self.log.split('\n')

        path = os.path.join(self.get_tmp_path(), 'log')
        if os.path.exists(path):
            return open(path).readlines()

        return []

    def show_duration(self):
        delta = self.finished_at - self.started_at
        return time.strftime("%H:%M:%S", time.gmtime(delta.seconds))

    def show_commit(self):
        return "{0}".format(self.commit[:10]) if self.commit else ''

    def __init__(self, *args, **kwargs):
        super(Deployment, self).__init__(*args, **kwargs)

        self.code = [self.stage.project.code, self.stage.code]
        for task in self.stage.tasks:
            self.code.append(task.code)
        self.code = '\n'.join(self.code)
