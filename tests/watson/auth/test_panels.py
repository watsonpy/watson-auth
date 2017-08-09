# -*- coding: utf-8 -*-
from tests.watson.auth import support
from watson.auth.panels import User
from watson.events.types import Event


class TestUserPanel(object):
    def test_create(self):
        panel = User({'enabled': True}, support.app.container.get('jinja2_renderer'), support.app)
        request = support.request
        request.user = support.admin_user
        panel.event = Event('test', params={'context': {'request': request}})
        assert panel.user == 'admin'
        assert panel.render_key_stat() == 'admin'
