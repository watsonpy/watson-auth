# -*- coding: utf-8 -*-
from io import BytesIO, BufferedReader
from tests.watson.auth import support


class TestRoute(object):
    def test_inject_user_id(self):
        support.app(
            support.sample_environ(PATH_INFO='/'),
            support.start_response)
        request = support.app.context['request']
        assert not request.user

        # login the user
        post_data = 'username=admin&password=test'
        environ = support.sample_environ(
            PATH_INFO='/login',
            REQUEST_METHOD='POST',
            HTTP_COOKIE='watson.session=1234',
            CONTENT_LENGTH=len(post_data))
        environ['wsgi.input'] = BufferedReader(
            BytesIO(post_data.encode('utf-8')))
        support.app(environ, support.start_response)
        request = support.app.context['request']
        assert request.user

        support.app(
            support.sample_environ(
                PATH_INFO='/',
                HTTP_COOKIE='watson.user=admin;watson.session=1234'),
            support.start_response)
        request = support.app.context['request']
        assert request.user
