from flask import Blueprint, render_template, request, redirect, url_for

from ..decorators import must_be_able_to
from ..extensions import db
from ..utils import notify, get_or_404
from ..stages.models import Stage

from .models import Task
from .forms import TaskForm

tasks = Blueprint('tasks', __name__, url_prefix='/tasks')


@tasks.route('/create', methods=['GET', 'POST'])
@must_be_able_to('create_task')
def create():
    stage_id = request.args.get('stage_id', None)
    stage = get_or_404(Stage, id=stage_id) if stage_id else None
    form = TaskForm(stages=[stage])

    if form.validate_on_submit():
        task = Task()
        form.populate_obj(task)
        db.session.add(task)
        db.session.commit()

        notify(u'Task "{0}" has been created.'.format(task.name),
               category='success', action='create_task')
        return redirect(url_for('tasks.view', id=task.id))

    return render_template('tasks/create.html', form=form, stage_id=stage_id)


@tasks.route('/view/<int:id>')
def view(id):
    task = get_or_404(Task, id=id)
    return render_template('tasks/view.html', task=task)


@tasks.route('/edit/<int:id>', methods=['GET', 'POST'])
@must_be_able_to('edit_task')
def edit(id):
    task = get_or_404(Task, id=id)
    form = TaskForm(request.form, task)

    if form.validate_on_submit():
        # Since we don't show deployments in form, we need to set them here.
        form.deployments.data = task.deployments
        form.populate_obj(task)
        db.session.add(task)
        db.session.commit()

        notify(u'Task "{0}" has been updated.'.format(task.name),
               category='success', action='edit_task')
        return redirect(url_for('tasks.view', id=task.id))

    return render_template('tasks/edit.html', task=task, form=form)


@tasks.route('/delete/<int:id>')
@must_be_able_to('delete_task')
def delete(id):
    task = get_or_404(Task, id=id)

    notify(u'Task "{0}" has been deleted.'.format(task.name),
           category='success', action='delete_task')

    db.session.delete(task)
    db.session.commit()

    return redirect(request.args.get('next')
                    or url_for('frontend.index'))


@tasks.route('/')
def all():
    tasks = Task.query.all()
    return render_template('tasks/all.html', tasks=tasks)
