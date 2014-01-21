# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, SmallInteger
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from watson.common import imports
from watson.framework.applications import Base
from watson.auth import authentication, authorization

Model = Base.global_app.container.get('sqlalchemy_declarative_base')


class RolePermission(Model):
    __tablename__ = 'roles_has_permissions'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    permission_id = Column(Integer,
                           ForeignKey('permissions.id'), primary_key=True)
    permission = relationship('Permission')
    value = Column(SmallInteger, default=0)
    created_date = Column(DateTime, default=datetime.now)


class UserPermission(Model):
    __tablename__ = 'users_has_permissions'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    permission_id = Column(Integer,
                           ForeignKey('permissions.id'), primary_key=True)
    permission = relationship('Permission')
    value = Column(SmallInteger, default=0)
    created_date = Column(DateTime, default=datetime.now)


class Role(Model):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    permissions = relationship('RolePermission',
                               backref='roles')
    created_date = Column(DateTime, default=datetime.now)

    def add_permission(self, permission, value=1):
        """Adds a permission to the role.

        Args:
            Permission permission: The permission to attach
            int value: The value to give the permission, can be either:
                        0 - deny
                        1 - allow
        """
        role_permission = RolePermission(value=value)
        role_permission.permission = permission
        self.permissions.append(role_permission)


class Permission(Model):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    key = Column(String(255))
    created_date = Column(DateTime, default=datetime.now)


users_has_roles = Table(
    'users_has_roles', Model.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id')),
    Column(
        'role_id',
        Integer,
        ForeignKey('roles.id'))
)


class UserMixin(object):

    """Common user fields, custom user classes should extend this as well as
    Model.

    Attributes:
        string id_field: The name of the field to use as the id for the user

    Columns:
        string _password: The password of the user, aliased by self.password
        string salt: The salt used to generate the password
        list roles: The roles associated with the user
        list permissions: The permissions associated with the user, overrides
                          the permissions associated with the role.
        date created_date: The time the user was created.
        date updated_date: The time the user was updated.
    """
    _acl = None
    id = Column(Integer, primary_key=True)
    _password = Column(String(255), name='password')
    salt = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now)

    @property
    def acl(self):
        """Convenience method to access the users ACL.

        See watson.auth.authorization.Acl for more information.
        """
        if not self._acl:
            self._acl = authorization.Acl(self)
        return self._acl

    @declared_attr
    def permissions(cls):
        return relationship('UserPermission', backref='user', cascade='all')

    @declared_attr
    def roles(cls):
        return relationship("Role",
                            secondary=users_has_roles,
                            backref="roles", cascade=None)

    @property
    def password(self):
        """Return the password.
        """
        return self._password

    @password.setter
    def password(self, password):
        """Automatically generates the hashed password and salt when set.

        Args:
            string password: The password to set.
        """
        _pass, salt = authentication.generate_password(password)
        self._password = _pass
        self.salt = salt

    def touch(self):
        """Updates the date the user was modified.
        """
        self.updated_date = datetime.now()

    def add_permission(self, permission, value=1):
        """Adds a permission to the user.

        This overrides any permission given by the associated roles.

        Args:
            Permission permission: The permission to attach
            int value: The value to give the permission, can be either:
                        0 - deny
                        1 - allow
        """
        user_permission = UserPermission(value=value)
        user_permission.permission = permission
        self.permissions.append(user_permission)

    def __repr__(self):
        return '<{0} id:{1}>'.format(imports.get_qualified_name(self), self.id)
