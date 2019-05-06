from flask.ext.wtf import Form
from wtforms.ext.sqlalchemy.orm import model_form

from ..extensions import db

from .models import Project

ProjectForm = model_form(Project, db.session, Form)
