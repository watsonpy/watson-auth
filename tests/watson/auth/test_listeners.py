# -*- coding: utf-8 -*-
from io import BytesIO, BufferedReader
from tests.watson.auth import support


class TestRoute(object):

    def test_inject_user_id(self):
        support.app(
            support.sample_environ(PATH_INFO='/'),
            support.start_response)
        request = support.app.container.get('request')
        assert not request.user
        # login the user
        environ = support.sample_environ(
            PATH_INFO='/login',
            REQUEST_METHOD='POST',
            HTTP_COOKIE='watson.session=1234')
        environ['wsgi.input'] = BufferedReader(
            BytesIO(b'username=admin&password=test'))
        support.app(environ, support.start_response)

        support.app(
            support.sample_environ(
                PATH_INFO='/',
                HTTP_COOKIE='watson.user=admin;watson.session=1234'),
            support.start_response)
        request = support.app.container.get('request')
        assert request.user
