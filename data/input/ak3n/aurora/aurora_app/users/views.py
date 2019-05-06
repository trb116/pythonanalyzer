from flask import Blueprint, render_template, redirect, url_for, request, g

from ..decorators import must_be_able_to
from ..extensions import db
from ..utils import notify, get_or_404

from .models import User
from .forms import EditUserForm, CreateUserForm

users = Blueprint('users', __name__, url_prefix='/users')


@users.route('/create', methods=['GET', 'POST'])
@must_be_able_to('create_user')
def create():
    form = CreateUserForm()

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)

        # Check for duplicates
        if User.query.filter_by(username=form.username.data).first() is None:
            db.session.add(user)
            db.session.commit()

            notify(u'User "{0}" has been created.'.format(user.username),
                   category='success', action='create_user')
            return redirect(url_for('users.view', id=user.id))
        form.username.errors = [u'Choose another username, please.']

    return render_template('users/create.html', form=form)


@users.route('/view/<int:id>')
def view(id):
    user = get_or_404(User, id=id)
    return render_template('users/view.html', user=user)


@users.route('/')
def all():
    users = User.query.all()
    return render_template('users/all.html', users=users)


@users.route('/delete/<int:id>')
@must_be_able_to('delete_user')
def delete(id):
    user = get_or_404(User, id=id)

    notify(u'User "{0}" has been deleted.'.format(user.username),
           category='success', action='delete_user')

    db.session.delete(user)
    db.session.commit()

    return redirect(request.args.get('next')
                    or url_for('frontend.index'))


@users.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    user = get_or_404(User, id=id)

    if not (g.user.can('edit_user') or user.id == g.user.id):
        notify(u"You can't do that. You don't have permission.",
               category='error', action='edit_user')

        return redirect(request.args.get('next')
                        or request.referrer
                        or url_for('frontend.index'))

    form = EditUserForm(request.form, user)

    if form.validate_on_submit():
        form.populate_obj(user)

        if form.password.data:
            user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        notify(u'User "{0}" has been updated.'.format(user.username),
               category='success', action='edit_user')
        return redirect(url_for('users.view', id=id))

    return render_template('users/edit.html', user=user, form=form)
