from flask.ext.wtf import (Form, Email, Required, TextField, BooleanField,
                           PasswordField)


class LoginForm(Form):
    email = TextField('Email', validators=[Required(), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Remember me', default=False)
