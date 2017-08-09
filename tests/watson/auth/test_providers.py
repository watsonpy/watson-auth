# -*- coding: utf-8 -*-
from watson.auth.providers import JWT
from watson.auth.providers import Session
from tests.watson.auth import support


class TestABCProvider(object):
    provider = None

    def setup(self):
        self.provider = Session(
            support.default_provider_settings,
            support.session)

    def test_user_model_identifier(self):
        assert self.provider.user_model_identifier == support.default_provider_settings['model']['identifier']

    def test_user_model(self):
        assert self.provider.user_model == support.TestUser

    def test_get_user(self):
        assert self.provider.get_user('admin') == support.admin_user
        assert not self.provider.get_user('admin2')

    def test_get_user_by_email_address(self):
        assert self.provider.get_user_by_email_address('admin') == support.admin_user
        assert not self.provider.get_user_by_email_address('admin2')

    def test_is_authorized(self):
        assert self.provider.is_authorized(support.admin_user)

    def test_authenticate_user(self):
        assert self.provider.authenticate('test', 'test')
        assert not self.provider.authenticate('test', 'testing')

    def test_authenticate_password_longer_max_length(self):
        assert not self.provider.authenticate('test', '1234567890123456789012345678901')


class TestSessionProvider(object):
    provider = None

    def setup(self):
        self.provider = Session(
            support.default_provider_settings,
            support.session)

    def test_handle_request(self):
        self.provider.handle_request(support.request)
        assert support.request.user

    def test_login(self):
        self.provider.login(support.admin_user, support.request)
        assert support.request.user == support.admin_user

    def test_logout(self):
        self.provider.login(support.admin_user, support.request)
        assert support.request.user == support.admin_user
        self.provider.logout(support.request)
        assert not support.request.user


class TestJWTProvider(object):
    provider = None

    def setup(self):
        self.provider = JWT(
            support.default_provider_settings,
            support.session)

    def test_login(self):
        token = self.provider.login(support.admin_user, support.request)
        assert token

    def test_handle_request(self):
        token = self.provider.login(support.admin_user, support.request)
        request = support.Request(
            support.sample_environ(
                HTTP_AUTHORIZATION='Bearer {}'.format(token)))
        self.provider.handle_request(request)
        assert request.user == support.admin_user

    def test_logout(self):
        token = self.provider.login(support.admin_user, support.request)
        request = support.Request(
            support.sample_environ(
                HTTP_AUTHORIZATION='Bearer {}'.format(token)))
        self.provider.handle_request(request)
        assert not self.provider.logout(request)
