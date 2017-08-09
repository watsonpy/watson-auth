# -*- coding: utf-8 -*-
from watson.auth import managers
from watson.auth.providers import Session
from tests.watson.auth import support


class TestForgottenPasswordTokenManager(object):

    provider = None
    manager = None

    def setup(self):
        self.provider = Session(
            support.default_provider_settings,
            support.session)
        self.manager = managers.ForgottenPasswordToken(
            mailer=support.app.container.get('mailer'),
            email_address_field='email')
        self.manager.provider = self.provider

    def test_create_token(self):
        user = self.provider.get_user('test')
        token = self.manager.create_token(
            user, request=support.request)
        assert token.user == user
        token = self.manager.get_token(token=token.token)
        assert token.user == user
