# -*- coding: utf-8 -*-
from watson.console import command, ConsoleError
from watson.console.decorators import arg
from watson.common import imports
from watson.db.session import NAME as session_name
from watson.db.contextmanagers import transaction_scope
from watson.di import ContainerAware
from watson.auth import authentication


class BaseAuthCommand(ContainerAware):
    __ioc_definition__ = {
        'init': {
            'config': lambda container: container.get('application.config')['auth']
        }
    }

    def __init__(self, config):
        self.config = config


def ensure_session_in_container(container, session):
    if not session:
        session = 'default'
    try:
        return container.get(session_name.format(session))
    except:
        raise ConsoleError('No database named {}'.format(session))


class Auth(command.Base, BaseAuthCommand):
    """Authentication commands.
    """
    name = 'auth'

    @arg('password')
    def generate_password(self, password):
        """Generates a password based on the application settings.
        """
        salt, new_password = authentication.generate_password(password)
        self.write('Generated hashed password from "{}"'.format(password))
        self.write('Password: {}'.format(new_password))
        self.write('Salt: {}'.format(salt))

    @arg('database', optional=True)
    def list_roles(self, database):
        """Lists all available roles.

        Args:
            database: The name of the database session.
        """
        session = ensure_session_in_container(self.container, database)
        from watson.auth.models import Role
        for role in session.query(Role):
            self.write('Role: {} (key: {})'.format(role.name, role.key))

    @arg('key')
    @arg('name')
    @arg('database', optional=True)
    def add_role(self, key, name, database):
        """Adds a new role to the database.

        Args:
            key: The identifier for the role
            name: The human readable name for the role
            database: The name of the database session.
        """
        session = ensure_session_in_container(self.container, database)
        from watson.auth.models import Role
        role = Role(key=key, name=name)
        with transaction_scope(session) as session:
            session.add(role)
            self.write('Role: {} (key: {}) added!'.format(name, key))

    @arg('key')
    @arg('name')
    @arg('database', optional=True)
    def add_permission(self, key, name, database):
        """Adds a new permission to the database.

        Args:
            key: The identifier for the permission
            name: The human readable name for the permission
            database: The name of the database session.
        """
        session = ensure_session_in_container(self.container, database)
        from watson.auth.models import Permission
        permission = Permission(key=key, name=name)
        with transaction_scope(session) as session:
            session.add(permission)
            self.write('Permission: {} (key: {}) added!'.format(name, key))

    @arg('permission_key')
    @arg('role_key')
    @arg('value', optional=True)
    @arg('database', optional=True)
    def add_permission_to_role(self, permission_key, role_key, value, database):
        """Attaches a permission to a role, with a default of False.

        Args:
            permission_key: The identifier for the permission
            role_key: The identifier for the permission
            value: The value of the permission (1 or 0)
            database: The name of the database session.
        """
        session = ensure_session_in_container(self.container, database)
        from watson.auth.models import Role
        from watson.auth.models import Permission
        permission = session.query(Permission).filter_by(key=permission_key).first()
        role = session.query(Role).filter_by(key=role_key).first()
        enabled = True if value else False
        role.add_permission(permission, value=enabled)
        session.commit()
        self.write(
            'Added permission {} ({}) to role {} ({}) with value: {}'.format(
                permission.name, permission.key,
                role.name, role.key,
                enabled))

    @arg('username')
    @arg('role_key')
    @arg('database', optional=True)
    def add_role_to_user(self, username, role_key, database):
        session = ensure_session_in_container(self.container, database)
        auth_authenticator = self.container.get('auth_authenticator')
        user = auth_authenticator.get_user(username)
        from watson.auth.models import Role
        role = session.query(Role).filter_by(key=role_key).first()
        user.roles.append(role)
        session.commit()
        self.write(
            'Added role {} ({}) to user {} ({})'.format(
                role.name, role.key,
                getattr(user, self.config['model']['columns']['username']),
                user.id))

    @arg('username')
    @arg('permission_key')
    @arg('value', optional=True)
    @arg('database', optional=True)
    def add_permission_to_user(self, username, permission_key, value, database):
        session = ensure_session_in_container(self.container, database)
        auth_authenticator = self.container.get('auth_authenticator')
        user = auth_authenticator.get_user(username)
        from watson.auth.models import Permission
        permission = session.query(Permission).filter_by(key=permission_key).first()
        enabled = True if value else False
        user.add_permission(permission, value=enabled)
        session.commit()
        self.write(
            'Added permission {} ({}) to user {} ({}) with value: {}'.format(
                permission.name, permission.key,
                getattr(user, self.config['model']['columns']['username']),
                user.id, enabled))

    @arg('username')
    @arg('password')
    @arg('database', optional=True)
    def create_user(self, username, password, database):
        """Create a new user.

        Args:
            username: The username of the user
            password: The password of the user
            database: The name of the database session.
        """
        session = ensure_session_in_container(self.container, database)
        db_config = self.config['model']
        user_model = db_config['class']
        model_class = imports.load_definition_from_string(user_model)
        with transaction_scope(session) as session:
            user = model_class()
            setattr(user, db_config['columns']['username'], username)
            setattr(user, 'password', password)
            session.add(user)
            self.write('Created user {}'.format(username))

    @arg('database', optional=True)
    def list_permissions(self, database):
        """Lists all available permissions.

        Args:
            database: The name of the database session.
        """
        session = ensure_session_in_container(self.container, database)
        from watson.auth.models import Permission
        for permission in session.query(Permission):
            self.write('Permission: {} (key: {})'.format(
                permission.name, permission.key))
