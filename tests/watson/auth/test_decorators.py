# -*- coding: utf-8 -*-
from io import BytesIO, BufferedReader
from wsgiref import util
from pytest import raises
from watson.events import types
from watson.http.messages import Request
from watson.framework import controllers, exceptions
from tests.watson.auth import support
from watson.auth.decorators import auth, login, logout


def start_response(status_line, headers):
    pass


def sample_environ(**kwargs):
    environ = {}
    util.setup_testing_defaults(environ)
    environ.update(**kwargs)
    return environ


class SampleController(controllers.Action):

    @auth
    def index_action(self):
        return 'index'

    @auth(roles='Admin')
    def admin_role_action(self):
        return 'admin role'

    @auth(permissions='create')
    def permissions_action(self):
        return 'permissions'

    @auth(roles='Admin', permissions='create')
    def permissions_role(self):
        return 'permissions and role'

    @auth(roles='Admin', unauthenticated_url='/unauthed-test')
    def unauthed_custom_url_action(self):
        pass

    @auth(roles='Admin', unauthorized_url='/unauthorized-test')
    def unauthorized_custom_url_action(self):
        pass

    @auth(roles='Admin', should_404=True)
    def unauthorized_404_action(self):
        pass

    @login
    def login_action(self):
        return 'login'

    @logout
    def logout_action(self):
        return 'logout'

    @logout(redirect_url='/custom-logout')
    def logout_custom_action(self):
        return 'logout'


class TestLogin(object):
    def setup(self):
        controller = support.app.container.get(
            'tests.watson.auth.test_decorators.SampleController')
        event = types.Event('test', params={
            'context': {
                'request': Request.from_environ(sample_environ(), 'watson.http.sessions.Memory')
            }
        })
        controller.event = event
        self.controller = controller

    def test_no_post(self):
        response = self.controller.login_action()
        assert response == 'login'

    def test_invalid_user(self):
        post_data = 'username=simon&password=test'
        environ = sample_environ(REQUEST_METHOD='POST',
                                 CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
        response = self.controller.login_action()
        assert response.headers['location'] == '/login'

    def test_invalid_form(self):
        post_data = 'username=simon'
        environ = sample_environ(REQUEST_METHOD='POST',
                                 CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
        self.controller.login_action()
        assert len(self.controller.flash_messages) == 1

    def test_valid_user(self):
        post_data = 'username=admin&password=test'
        environ = sample_environ(REQUEST_METHOD='POST',
                                 CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
        response = self.controller.login_action()
        assert response.headers['location'] == '/'

    def test_already_authenticated_user(self):
        self.controller.request.user = support.regular_user
        response = self.controller.login_action()
        assert response.headers['location'] == '/'


class TestLogout(object):
    def setup(self):
        post_data = 'username=admin&password=test'
        environ = sample_environ(REQUEST_METHOD='POST',
                                 CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller = support.app.container.get(
            'tests.watson.auth.test_decorators.SampleController')
        self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
        self.controller.login_action()

    def test_logout(self):
        self.controller.logout_action()
        assert not self.controller.request.user

    def test_redirect_logout(self):
        response = self.controller.logout_custom_action()
        assert response.headers['location'] == '/custom-logout'


class TestAuth(object):

    def setup(self):
        controller = support.app.container.get(
            'tests.watson.auth.test_decorators.SampleController')
        controller.request = Request.from_environ(sample_environ(), 'watson.http.sessions.Memory')
        self.controller = controller

    def test_unauthenticated(self):
        response = self.controller.index_action()
        assert response.headers['location'] == '/login'

    def test_authenticated(self):
        self.controller.request.session['watson.user'] = 'regular'
        response = self.controller.index_action()
        assert response == 'index'

    def test_authenticated_injected_user(self):
        self.controller.request.session['watson.user'] = 'someone'
        response = self.controller.index_action()
        assert response.headers['location'] == '/login'

    def test_authenticated_no_matching_role(self):
        self.controller.request.session['watson.user'] = 'regular'
        response = self.controller.admin_role_action()
        assert response.headers['location'] == '/unauthorized'

    def test_authenticated_matching_role(self):
        self.controller.request.session['watson.user'] = 'admin'
        response = self.controller.admin_role_action()
        assert response == 'admin role'

    def test_authenticated_no_matching_permission(self):
        self.controller.request.session['watson.user'] = 'regular'
        response = self.controller.permissions_action()
        assert response.headers['location'] == '/unauthorized'

    def test_authenticated_matching_permission(self):
        self.controller.request.session['watson.user'] = 'admin'
        response = self.controller.permissions_action()
        assert response == 'permissions'

    def test_authenticated_matching_role_permission(self):
        self.controller.request.session['watson.user'] = 'admin'
        response = self.controller.permissions_role()
        assert response == 'permissions and role'

    def test_unauthenticated_custom_url(self):
        response = self.controller.unauthed_custom_url_action()
        assert response.headers['location'] == '/unauthed-test'

    def test_unauthorized_custom_url(self):
        self.controller.request.session['watson.user'] = 'regular'
        response = self.controller.unauthorized_custom_url_action()
        assert response.headers['location'] == '/unauthorized-test'

    def test_raises_404_unauthorized(self):
        with raises(exceptions.NotFoundError):
            self.controller.request.session['watson.user'] = 'regular'
            self.controller.unauthorized_404_action()
