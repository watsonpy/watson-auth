# -*- coding: utf-8 -*-
from watson.auth import forms


class TestForms(object):

    def test_login(self):
        login = forms.Login()
        assert login

    def test_forgotten_password(self):
        forgotten_password = forms.ForgottenPassword()
        assert forgotten_password

    def test_reset_password(self):
        reset_password = forms.ResetPassword()
        assert reset_password
