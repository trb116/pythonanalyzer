import json

from flask import Blueprint, render_template, url_for, redirect, request, g

from ..decorators import must_be_able_to
from ..extensions import db
from ..utils import get_or_404, notify

from .models import Project, ProjectParameter
from .exceptions import ParameterValueError
from .forms import ProjectForm
from .tasks import clone_repository, remove_repository

projects = Blueprint('projects', __name__, url_prefix='/projects')


@projects.route('/create', methods=['GET', 'POST'])
@must_be_able_to('create_project')
def create():
    form = ProjectForm()

    if form.validate_on_submit():
        project = Project()
        form.populate_obj(project)
        db.session.add(project)
        db.session.commit()

        project.create_default_params()

        notify(u'Project "{0}" has been created.'.format(project.name),
               category='success', action='create_project')
        return redirect(url_for('projects.view', id=project.id))

    return render_template('projects/create.html', form=form)


@projects.route('/view/<int:id>')
def view(id):
    project = get_or_404(Project, id=id)
    return render_template('projects/view.html', project=project)


@projects.route('/edit/<int:id>', methods=['GET', 'POST'])
@must_be_able_to('edit_project')
def edit(id):
    project = get_or_404(Project, id=id)
    form = ProjectForm(request.form, project)

    if form.validate_on_submit():
        form.params.data = project.params
        form.populate_obj(project)
        db.session.add(project)
        db.session.commit()

        notify(u'Project "{0}" has been updated.'.format(project.name),
               category='success', action='edit_project')
        return redirect(url_for('projects.view', id=id))

    return render_template('projects/edit.html', project=project, form=form)


@projects.route('/delete/<int:id>')
@must_be_able_to('delete_project')
def delete(id):
    project = get_or_404(Project, id=id)

    # Delete stages
    for stage in project.stages:
        db.session.delete(stage)
    # Delete params
    for param in project.params:
        db.session.delete(param)
    db.session.delete(project)
    db.session.commit()
    
    notify(u'Project "{0}" has been deleted.'.format(project.name),
           category='success', action='delete_project')

    return redirect(request.args.get('next')
                    or url_for('frontend.index'))

TASKS = {
    'clone_repository': clone_repository,
    'remove_repository': remove_repository
}


@projects.route('/execute/<int:id>', methods=['POST'])
def execute(id):
    project = get_or_404(Project, id=id)
    action = request.form.get('action')
    if g.user.can(action):
        if action == 'edit_project':
            name, value = request.form.get('name'), request.form.get('value')
            parameter = ProjectParameter.query.filter_by(name=name).first()

            try:
                parameter.set_value(value)
                db.session.add(parameter)
                db.session.commit()
            except ParameterValueError as e:
                notify(e.message, category='error', action='edit_project')
                return json.dumps({'error': True})
        else:
            TASKS[action](project)
        return json.dumps({'error': False})

    notify(u"""You can't execute "{0}.{1}".""".format(project.name, action),
           category='error', action=action, user_id=g.user.id)
    return json.dumps({'error': True})


@projects.route('/commits/<int:id>')
def commits(id):
    project = get_or_404(Project, id=id)
    branch = request.args.get('branch')
    query = request.args.get('query')
    page_limit = int(request.args.get('page_limit'))
    page = int(request.args.get('page'))

    if query:
        commits = project.get_all_commits(branch,
                                          skip=page_limit * page)
    else:
        commits = project.get_commits(branch, max_count=page_limit,
                                      skip=page_limit * (page - 1))

    result = []
    for commit in commits:
        if query and not (query in commit.hexsha or query in commit.message):
            continue
        else:
            result.append({'id': commit.hexsha,
                           'message': commit.message,
                           'title': "{0} - {1}".format(commit.hexsha[:10],
                                                       commit.message)})

    total = project.get_commits_count(branch)
    if query:
        total = len(result)
        result = result[:page_limit]

    return json.dumps({'total': total,
                       'commits': result})


@projects.route('/commits/one/<int:id>/<string:branch>/<string:commit>')
def get_one_commit(id, branch, commit):
    project = get_or_404(Project, id=id)
    commits = project.get_all_commits(branch)
    for item in commits:
        if commit == item.hexsha:
            return json.dumps({'id': item.hexsha,
                               'message': item.message,
                               'title': "{0} - {1}".format(item.hexsha[:10],
                                                           item.message)})
    return 'error', 500


@projects.route('/')
def all():
    projects = Project.query.all()
    return render_template('projects/all.html', projects=projects)
