from tests.watson.auth import support
from watson.auth import authorization


class TestAcl(object):

    def test_register_user_against_acl(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.user is support.regular_user

    def test_user_has_roles(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.has_role('Regular') is True

    def test_user_doesnt_have_role(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.has_role('Admin') is False

    def test_user_has_one_role_of(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.has_role(('Regular', 'Guest'))

    def test_user_has_no_role_of(self):
        acl = authorization.Acl(support.regular_user)
        assert not acl.has_role(('Admin', 'Guest'))

    def test_user_has_inherited_permission(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.has_permission('read')
        assert acl.permissions['delete'].inherited == 1

    def test_user_has_explicit_permission(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.has_permission('read')
        assert acl.permissions['read'].inherited == 0

    def test_user_has_explicit_permission_deny(self):
        acl = authorization.Acl(support.regular_user)
        assert not acl.has_permission('create')

    def test_invalid_permission(self):
        acl = authorization.Acl(support.regular_user)
        acl.allow_default = False
        assert not acl.has_permission('Invalid Permission')

    def test_invalid_permission_allow_default(self):
        acl = authorization.Acl(support.regular_user)
        assert acl.has_permission('Invalid Permission')

    def test_user_multiple_roles(self):
        acl = authorization.Acl(support.complex_user)
        assert acl.has_permission('create')
        assert not acl.has_permission('delete')
        assert acl.has_role('Guest')
        assert acl.has_role('Admin')
