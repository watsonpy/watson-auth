# -*- coding: utf-8 -*-
from watson import form
from watson.form import fields
from watson.auth import validators


class Login(form.Form):
    """A standard login form containing username and password fields.
    """
    username = fields.Text(required=True, label='Username')
    password = fields.Password(required=True, label='Password')
    submit = fields.Submit(button_mode=True, label='Login')


class ForgottenPassword(form.Form):
    """A standard forgotten password form.
    """
    username = fields.Text(required=True, label='Username')
    submit = fields.Submit(
        button_mode=True,
        label='Request Reset')


class ResetPassword(form.Form):
    """A standard reset password form.
    """
    password = fields.Password(
        required=True,
        validators=[validators.Match(field='confirm_password')],
        label='Password')
    confirm_password = fields.Password(required=True, label='Confirm Password')
    submit = fields.Submit(button_mode=True, label='Reset')
