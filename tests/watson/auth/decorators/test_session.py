# -*- coding: utf-8 -*-
from io import BytesIO, BufferedReader
from pytest import raises
from watson.auth.providers.session.decorators import auth, login, logout, forgotten, reset
from watson.events import types
from watson.framework import controllers, exceptions
from tests.watson.auth import support


class SampleController(controllers.Action):

    @auth(login_redirect='login')
    def index_action(self):
        return 'index'

    @login
    def login_action(self, form):
        return 'login'

    @logout
    def logout_action(self):
        return 'logout'

    @logout(redirect='/custom-logout')
    def logout_custom_action(self):
        return 'logout'


class BaseDecoratorCase(object):
    def setup(self):
        controller = support.app.container.get(
            'tests.watson.auth.decorators.test_session.SampleController')
        event = types.Event('test', params={
            'context': {
                'request': self._generate_request()
            }
        })
        controller.event = event
        self.controller = controller

    def _generate_request(self, **kwargs):
        request = support.Request.from_environ(
            support.sample_environ(**kwargs), 'watson.http.sessions.Memory')
        request.user = None
        return request


class TestLogin(BaseDecoratorCase):
    def test_no_post(self):
        response = self.controller.login_action()
        assert response == 'login'

    def test_invalid_user(self):
        post_data = 'username=simon&password=test'
        environ = support.sample_environ(
            PATH_INFO='/login',
            REQUEST_METHOD='POST',
            CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = self._generate_request(**environ)
        response = self.controller.login_action()
        assert response.headers['location'].endswith('/login')

    def test_invalid_form(self):
        post_data = 'username=simon'
        environ = support.sample_environ(
            REQUEST_METHOD='POST',
            CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = self._generate_request(**environ)
        self.controller.login_action()
        assert len(self.controller.flash_messages) == 1

    def test_valid_user(self):
        post_data = 'username=admin&password=test'
        environ = support.sample_environ(
            REQUEST_METHOD='POST',
            CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = self._generate_request(**environ)
        response = self.controller.login_action()
        assert response.headers['location'] == '/'

    def test_already_authenticated_user(self):
        self.controller.request.user = support.regular_user
        response = self.controller.login_action()
        assert response.headers['location'] == '/'

    def test_login_redirect_to_referrer(self):
        post_data = 'username=admin&password=test'
        environ = support.sample_environ(
            REQUEST_METHOD='POST',
            CONTENT_LENGTH=len(post_data),
            PATH_INFO='/login',
            QUERY_STRING='redirect=http%3A%2F%2F127.0.0.1%2Fexisting-url%253Fto-here%2526and-here')
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller.request = self._generate_request(**environ)
        response = self.controller.login_action()
        assert response.headers['location'].endswith('/existing-url?to-here&and-here')


class TestLogout(BaseDecoratorCase):
    def setup(self):
        post_data = 'username=admin&password=test'
        environ = support.sample_environ(
            REQUEST_METHOD='POST',
            CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        self.controller = support.app.container.get(
            'tests.watson.auth.decorators.test_session.SampleController')
        self.controller.request = self._generate_request(**environ)
        self.controller.login_action()

    def test_logout(self):
        self.controller.logout_action()
        assert not self.controller.request.user

    def test_redirect_logout(self):
        response = self.controller.logout_custom_action()
        assert response.headers['location'] == '/custom-logout'


class TestAuth(BaseDecoratorCase):
    def test_unauthenticated(self):
        response = self.controller.index_action()
        assert response.headers['location'].startswith('/login')

    # def test_authenticated(self):
    #     self.controller.request.session['watson.user'] = 'regular'
    #     response = self.controller.index_action()
    #     assert response == 'index'

    # def test_authenticated_injected_user(self):
    #     self.controller.request.session['watson.user'] = 'someone'
    #     response = self.controller.index_action()
    #     assert response.headers['location'] == '/login'

    # def test_authenticated_no_matching_role(self):
    #     self.controller.request.session['watson.user'] = 'regular'
    #     response = self.controller.admin_role_action()
    #     assert response.headers['location'] == 'unauthorized'

    # def test_authenticated_matching_role(self):
    #     self.controller.request.session['watson.user'] = 'admin'
    #     response = self.controller.admin_role_action()
    #     assert response == 'admin role'

    # def test_authenticated_no_matching_permission(self):
    #     self.controller.request.session['watson.user'] = 'regular'
    #     response = self.controller.permissions_action()
    #     assert response.headers['location'] == 'unauthorized'

    # def test_authenticated_matching_permission(self):
    #     self.controller.request.session['watson.user'] = 'admin'
    #     response = self.controller.permissions_action()
    #     assert response == 'permissions'

    # def test_authenticated_matching_role_permission(self):
    #     self.controller.request.session['watson.user'] = 'admin'
    #     response = self.controller.permissions_role()
    #     assert response == 'permissions and role'

    # def test_unauthenticated_custom_url(self):
    #     response = self.controller.unauthed_custom_url_action()
    #     assert response.headers['location'] == '/unauthed-test'

    # def test_unauthorized_custom_url(self):
    #     self.controller.request.session['watson.user'] = 'regular'
    #     response = self.controller.unauthorized_custom_url_action()
    #     assert response.headers['location'] == '/unauthorized-test'

    # def test_raises_404_unauthorized(self):
    #     with raises(exceptions.NotFoundError):
    #         self.controller.request.session['watson.user'] = 'regular'
    #         self.controller.unauthorized_404_action()

    # def test_redirect_to_login_with_existing_url(self):
    #     environ = support.sample_environ(
    #         PATH_INFO='/existing-url', QUERY_STRING='to-here&and-here')
    #     self.controller.request = self._generate_request(**environ)
    #     response = self.controller.unauthed_url_redirect()
    #     assert response.headers['location'] == 'login?redirect=http%3A%2F%2F127.0.0.1%2Fexisting-url%3Fto-here%26and-here'

    # def test_valid_requires(self):
    #     self.controller.request.session['watson.user'] = 'regular'
    #     assert self.controller.valid_action() == 'valid'

    # def test_invalid_requires(self):
    #     self.controller.request.session['watson.user'] = 'regular'
    #     response = self.controller.invalid_action()
    #     assert response.headers['location'] == '/unauthorized-test'

# class TestForgottenPassword(object):

#     def setup(self):
#         controller = support.app.container.get(
#             'tests.watson.auth.test_decorators.SampleController')
#         controller.request = Request.from_environ(sample_environ(), 'watson.http.sessions.Memory')
#         self.controller = controller

#     def test_valid_user(self):
#         post_data = 'username=test'
#         environ = sample_environ(PATH_INFO='/forgotten-password',
#                                  REQUEST_METHOD='POST',
#                                  CONTENT_LENGTH=len(post_data))
#         environ['wsgi.input'] = BufferedReader(
#             BytesIO(post_data.encode('utf-8')))
#         self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
#         response = self.controller.forgotten_action()
#         assert response.headers['location'] == 'http://127.0.0.1/forgotten-password'

#     def test_invalid_user(self):
#         post_data = 'username=doesnt_exist'
#         environ = sample_environ(PATH_INFO='/forgotten-password',
#                                  REQUEST_METHOD='POST',
#                                  CONTENT_LENGTH=len(post_data))
#         environ['wsgi.input'] = BufferedReader(
#             BytesIO(post_data.encode('utf-8')))
#         self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
#         response = self.controller.forgotten_action()
#         assert response == 'forgotten'


# class TestResetPassword(object):
#     def setup(self):
#         controller = support.app.container.get(
#             'tests.watson.auth.test_decorators.SampleController')
#         controller.request = Request.from_environ(sample_environ(), 'watson.http.sessions.Memory')
#         self.controller = controller

#     def test_valid_token(self):
#         authenticator = support.app.container.get('auth_authenticator')
#         manager = managers.ForgottenPasswordToken(
#             config=support.app.container.get('application.config')['auth']['forgotten_password'],
#             session=authenticator.session,
#             mailer=support.app.container.get('mailer'),
#             email_field='email')
#         user = authenticator.get_user('test')
#         token = manager.create_token(
#             user, request=support.request)
#         post_data = 'password=test1&confirm_password=test1'
#         environ = sample_environ(PATH_INFO='/reset-password',
#                                  QUERY_STRING='token={}'.format(token.token),
#                                  REQUEST_METHOD='POST',
#                                  CONTENT_LENGTH=len(post_data))
#         environ['wsgi.input'] = BufferedReader(
#             BytesIO(post_data.encode('utf-8')))
#         self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
#         response = self.controller.reset_action()
#         assert response.headers['location'] == '/'

#     def test_invalid_token(self):
#         post_data = ''
#         environ = sample_environ(PATH_INFO='/reset-password',
#                                  REQUEST_METHOD='POST',
#                                  CONTENT_LENGTH=len(post_data))
#         environ['wsgi.input'] = BufferedReader(
#             BytesIO(post_data.encode('utf-8')))
#         self.controller.request = Request.from_environ(environ, 'watson.http.sessions.Memory')
#         response = self.controller.reset_action()
#         assert response.headers['location'] == '/'
