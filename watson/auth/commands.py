# -*- coding: utf-8 -*-
from watson.console import command, ConsoleError
from watson.console.decorators import arg
from watson.db.session import NAME as session_name
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
    def genpass(self, password):
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
