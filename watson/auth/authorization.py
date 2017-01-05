# -*- coding: utf-8 -*-
import collections


Permission = collections.namedtuple('Permission', 'id name inherited value')


class Acl(object):

    """Access Control List functionality for managing users' roles and
    permissions.

    By default, the user model contains an `acl` attribute, which allows
    access to the Acl object.

    Attributes:
        allow_default (boolean): Whether or not to allow/deny access if the
                                 permission has not been set on that role.

    """
    allow_default = True
    _permissions = None

    def __init__(self, user):
        """Initializes the Acl.

        Args:
            watson.auth.models.UserMixin user: The user to validate against
        """
        self.user = user

    @property
    def permissions(self):
        if not self._permissions:
            self._generate_user_permissions()
        return self._permissions

    def has_role(self, role_key):
        """Validates a role against the associated roles on a user.

        Args:
            role_key (string|tuple|list): The role(s) to validate against.
        """
        for role in self.user.roles:
            if isinstance(role_key, (list, tuple)) and role.key in role_key:
                return True
            elif role.key == role_key:
                return True
        return False

    def has_permission(self, permission):
        """Check to see if a user has a specific permission.

        If the permission has not been set, then it access will be granted
        based on the allow_default attribute.

        Args:
            permission (string): The permission to find.
        """
        if permission not in self.permissions.keys():
            return self.allow_default
        if not self.permissions[permission].value:
            return False
        return True

    def _generate_user_permissions(self):
        """Internal method to generate the permissions for the user.

        Retrieve all the permissions associated with the users roles, and then
        merge the users individual permissions to overwrite the inherited
        role permissions.
        """
        permissions = {}
        for role in self.user.roles:
            permissions.update(
                {permission.permission.key: Permission(
                    id=permission.permission_id,
                    name=permission.permission.name,
                    inherited=1,
                    value=permission.value)
                    for permission in role.permissions})
        permissions.update(
            {permission.permission.key: Permission(
                id=permission.permission_id,
                name=permission.permission.name,
                inherited=0, value=permission.value)
                for permission in self.user.permissions})
        self._permissions = permissions
