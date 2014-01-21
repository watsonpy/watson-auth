# -*- coding: utf-8 -*-
from watson import form
from watson.form import fields


class Login(form.Form):
    """A standard login form containing username and password fields.
    """
    username = fields.Text(required=True)
    password = fields.Password(required=True)
    login = fields.Submit(button_mode=True)
