# -*- coding: utf-8 -*-
from wsgiref import util
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from watson.framework import applications, events, controllers
from watson.auth.decorators import login


def start_response(status_line, headers):
    pass


def sample_environ(**kwargs):
    environ = {}
    util.setup_testing_defaults(environ)
    environ.update(kwargs)
    return environ

app_config = {
    'debug': {
        'enabled': True
    },
    'db': {
        'connections': {
            'default': {
                'connection_string': 'sqlite:///:memory:',
                'engine_options': {
                    'echo': False
                }
            }
        }
    },
    'auth': {
        'db': {
            'user_model': 'tests.watson.auth.support.TestUser'
        }
    },
    'routes': {
        'home': {
            'path': '/',
            'options': {
                'controller': 'tests.watson.auth.support.TestController'
            }
        },
        'login': {
            'path': '/login',
            'options': {
                'controller': 'tests.watson.auth.support.TestController'
            }
        }
    },
    'session': {
        'class': 'watson.http.sessions.Memory'
    },
    'views': {
        'templates': {
            'testcontroller/get': 'blank'
        }
    },
    'events': {
        events.INIT: [
            ('watson.auth.listeners.Init', 1, True)
        ],
    }
}

# Initialize a sample application
app = applications.Http(app_config)


class TestController(controllers.Rest):
    def GET(self):
        pass

    @login
    def POST(self):
        pass


# Create a sample user
from watson.auth import models


class TestUser(models.UserMixin, models.Model):
    """A sample user class.
    """
    __tablename__ = 'users'
    username = Column(String(255), unique=True)


# Create the schema
engine = app.container.get('sqlalchemy_engine_default')
models.Model.metadata.drop_all(engine)
models.Model.metadata.create_all(engine)

session = app.container.get('sqlalchemy_session_default')

# Add some roles
role_guest = models.Role(name='Guest', key='guest')
role_regular = models.Role(name='Regular', key='regular')
role_admin = models.Role(name='Admin', key='admin')
session.add(role_guest)
session.add(role_regular)
session.add(role_admin)

# Add some permissions
permission_create = models.Permission(name='Create', key='create')
permission_delete = models.Permission(name='Delete', key='delete')
permission_read = models.Permission(name='Read', key='read')
session.add(permission_create)
session.add(permission_delete)
session.add(permission_read)

# Add the permissions to the roles
role_admin.add_permission(permission_create)
role_admin.add_permission(permission_read)
role_admin.add_permission(permission_delete)

role_regular.add_permission(permission_create)
role_regular.add_permission(permission_read)
role_regular.add_permission(permission_delete)

role_guest.add_permission(permission_read)


# Add a sample user
guest_user = TestUser(username='test', password='test')
guest_user.roles.append(role_guest)
session.add(guest_user)
admin_user = TestUser(username='admin', password='test')
admin_user.roles.append(role_admin)
session.add(admin_user)
regular_user = TestUser(username='regular', password='test')
regular_user.roles.append(role_regular)
regular_user.add_permission(permission_create, 0)
regular_user.add_permission(permission_read, 1)
session.add(regular_user)

# Add a user with multiple roles
complex_user = TestUser(username='complex', password='test')
complex_user.roles.append(role_guest)
complex_user.roles.append(role_admin)
complex_user.add_permission(permission_delete, 0)

session.commit()
