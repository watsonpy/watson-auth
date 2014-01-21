# -*- coding: utf-8 -*-
from tests.watson.auth import support


class TestCreateUser(object):
    session = None

    def setup(self):
        self.session = support.app.container.get('sqlalchemy_session_default')

    def test_create(self):
        found_user = self.session.query(support.TestUser)\
                         .filter(support.TestUser.username == 'test').one()
        found_user.touch()
        assert found_user
        assert repr(found_user) == '<tests.watson.auth.support.TestUser id:1>'

    def test_user_has_acl(self):
        user = support.regular_user
        assert user.acl
