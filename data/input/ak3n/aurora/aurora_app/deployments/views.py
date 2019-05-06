import json
from datetime import datetime

from flask import (Blueprint, Response, render_template, request, g, redirect,
                   url_for)

from ..utils import get_or_404, notify, build_log_result
from ..extensions import db
from ..decorators import must_be_able_to
from ..stages.models import Stage
from ..tasks.models import Task

from .tasks import deploy
from .models import Deployment
from .constants import STATUSES

deployments = Blueprint('deployments', __name__, url_prefix='/deployments')

current_deployments = {}


@deployments.route('/create/stage/<int:id>', methods=['POST', 'GET'])
@must_be_able_to('create_deployment')
def create(id):
    stage = get_or_404(Stage, id=id)
    clone_id = request.args.get('clone')

    if request.method == 'POST':
        tasks_ids = request.form.getlist('selected')

        if tasks_ids == []:
            return "You must select tasks for deployment."

        tasks = [get_or_404(Task, id=int(task_id)) for task_id in tasks_ids]
        branch = request.form.get('branch')
        commit = request.form.get('commit')

        if not commit and stage.project.get_repo() is not None:
            commit = stage.project.get_last_commit(branch).hexsha

        deployment = Deployment(stage=stage, tasks=tasks,
                                branch=branch, user=g.user, commit=commit,
                                status=STATUSES['RUNNING'])
        db.session.add(deployment)
        db.session.commit()

        deploy(deployment.id)
        return redirect(url_for('deployments.view', id=deployment.id))

    if stage.project.get_or_create_parameter_value('fetch_before_deploy')\
            == 'True':
        # Fetch
        stage.project.fetch()

    branches = stage.project.get_branches()
    if clone_id:
        clone_deployment = get_or_404(Deployment, id=clone_id)

        if clone_deployment.stage.id != stage.id:
            return "Clone deployment should have the same stage."

        # Select clone deployment's branch
        branch = None
        if branches:
            for branch_item in branches:
                if branch_item.name == clone_deployment.branch:
                    branch = branch_item
    else:
        clone_deployment = None
        branch = branches[0] if branches else None

    return render_template('deployments/create.html', stage=stage,
                           branch=branch, clone_deployment=clone_deployment)


@deployments.route('/view/<int:id>')
def view(id):
    deployment = get_or_404(Deployment, id=id)
    return render_template('deployments/view.html', deployment=deployment)


@deployments.route('/code/<int:id>/fabfile.py')
def raw_code(id):
    deployment = get_or_404(Deployment, id=id)
    return Response(deployment.code, mimetype='text/plain')


@deployments.route('/log/<int:id>')
def log(id):
    """
    Function for getting log for deployment in real time.
    Built on server-sent events.
    """
    deployment = get_or_404(Deployment, id=id)
    last_event_id = request.args.get('lastEventId')

    lines = deployment.get_log_lines()
    # If client just connected return all existing log
    result = ['id: {0}'.format(len(lines))]
    if not last_event_id:
        result.extend(build_log_result(lines))
    # else return new lines.
    else:
        new_lines = lines[int(last_event_id):]
        result.extend(build_log_result(new_lines))

    # len(result) == 1 means that no new lines were added
    # and then deployment's log is not updating.
    if len(result) == 1:
        status = deployment.show_status()
        result = 'data: {"event": "finished", "status": "' + status + '"}\n'
    else:
        result = '\n'.join(result)

    return Response(result + '\n\n', mimetype='text/event-stream')


@deployments.route('/stop', methods=['POST'])
def cancel():
    id = request.form.get('id')
    deployment = get_or_404(Deployment, id=id)
    action = 'cancel_deployment'
    if g.user.can(action) and id:
        try:
            current_deployments[id].terminate()
            current_deployments[id].join()
            current_deployments.pop(id)

            deployment.log = '\n'.join(deployment.get_log_lines())
            deployment.log += "Deployment has canceled."
            deployment.finished_at = datetime.now()
            deployment.status = STATUSES['CANCELED']

            db.session.add(deployment)
            db.session.commit()

            message = "Deployment has canceled successfully."
            category = 'success'
        except Exception, e:
            message = "Can't cancel deployment.\n" + \
                      "Error: {0}".format(e.message)
            category = 'error'

        notify(message, category=category, action=action)
        return json.dumps({'error': True if category == 'error' else False})

    notify("You can't execute this action.", category='error', action=action)
    return json.dumps({'error': True})
