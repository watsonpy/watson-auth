# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        SmallInteger)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from watson.common import imports
from watson.auth import authentication, authorization
from watson.db.models import Model
from watson.db.utils import _table_attr


class Permission(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    key = Column(String(255))
    created_date = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<{0} key:{1} name:{2}>'.format(
            imports.get_qualified_name(self), self.key, self.name)


class Role(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    key = Column(String(255))
    permissions = relationship('RolesHasPermission',
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
        role_permission = RolesHasPermission(value=value)
        role_permission.permission = permission
        self.permissions.append(role_permission)

    def __repr__(self):
        return '<{0} key:{1} name:{2}>'.format(
            imports.get_qualified_name(self), self.key, self.name)


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
    __tablename__ = 'users'
    _acl_class = authorization.Acl
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
            self._acl = self._acl_class(self)
        return self._acl

    @declared_attr
    def permissions(cls):
        return relationship(UsersHasPermission, backref='user', cascade='all')

    @declared_attr
    def roles(cls):
        return relationship(Role,
                            secondary=UsersHasRole.__tablename__,
                            backref='roles', cascade=None)

    @declared_attr
    def forgotten_password_tokens(cls):
        return relationship(ForgottenPasswordToken, backref='user', cascade='all')

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
        user_permission = UsersHasPermission(value=value)
        user_permission.permission = permission
        self.permissions.append(user_permission)

    def __repr__(self):
        return '<{0} id:{1}>'.format(imports.get_qualified_name(self), self.id)


class RolesHasPermission(Model):
    role_id = Column(Integer,
                     ForeignKey(_table_attr(Role, 'id')),
                     primary_key=True)
    permission_id = Column(Integer,
                           ForeignKey(_table_attr(Permission, 'id')),
                           primary_key=True)
    permission = relationship(Permission)
    value = Column(SmallInteger, default=0)
    created_date = Column(DateTime, default=datetime.now)


class UsersHasPermission(Model):
    user_id = Column(Integer,
                     ForeignKey(_table_attr(UserMixin, 'id')),
                     primary_key=True)
    permission_id = Column(Integer,
                           ForeignKey(_table_attr(Permission, 'id')),
                           primary_key=True)
    permission = relationship(Permission)
    value = Column(SmallInteger, default=0)
    created_date = Column(DateTime, default=datetime.now)


class UsersHasRole(Model):
    user_id = Column(Integer,
                     ForeignKey(_table_attr(UserMixin, 'id')),
                     primary_key=True)
    role_id = Column(Integer,
                     ForeignKey(_table_attr(Role, 'id')),
                     primary_key=True)


class ForgottenPasswordToken(Model):
    id = Column(Integer, primary_key=True)
    token = Column(String(255))
    user_id = Column(Integer,
                     ForeignKey(_table_attr(UserMixin, 'id')))
    created_date = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<{0} user id:{1}>'.format(
            imports.get_qualified_name(self), self.user.id)
