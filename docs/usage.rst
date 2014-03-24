Usage
=====

A few things need to be configured from within the IocContainer of your
application before beginning.

1. An INIT application event listener must be added to your applications
   events. This injects some default configuration into your application
   and creates a new dependency in the IocContainer.

   ::

       'events': {
           events.INIT: [
               ('watson.auth.listeners.Init', 1, True)
           ],
       }

2. Configure the user model that you're going to use. Make sure that it
   subclasses ``watson.auth.models.UserMixin``.

   ::

       'auth': {
           'db': {
               'user_model': 'tests.watson.auth.support.TestUser'
           }
       }

The default configuration (below) can be overridden in your applications
config if required.

::

    'auth': {
        'db': {
                'username_field': 'username',
                'session': 'default',
        },
        'url': {
            'unauthenticated': '/login',
            'unauthorized': '/unauthorized',
            'logout': '/logout',
            'login': '/login',
            'login_success': '/',
        },
        'form': {
            'class': 'watson.auth.forms.Login',
            'username': 'username',
            'password': 'password',
            'invalid_message': 'Invalid username and/or password.'
        },
        'session': {
            'key': 'watson.user'
        },
        'password': {
            'max_length': 30
        }
    }

Note that any of the url's above can also be named routes.

Authentication
~~~~~~~~~~~~~~

There are several steps to authentication, the first being logging in a
user. To do this, add the ``login`` decorator to the action in your
controller that renders the login view.

::

    from watson.auth.decorators import login, logout
    from watson.auth import forms
    from watson.framework import controllers

    class Public(controllers.Action):

        @login
        def login_action(self):
            # handle the displaying of the form in the view
            form = forms.Login(action=self.url('login'))
            return {'form': form}

``@login`` also accepts the following arguments:

-  method: Can be any valid HTTP method
-  form\_class: The fully qualified class name of the form being used
-  auto\_redirect: Whether or not to redirect to
   config['auth']['url']['login\_success']

You'll also want to be able to logout a user, so add the ``logout``
decorator to the logout action as well.

::

    @logout(redirect_url='/')
    def logout_action(self):
        pass

Make sure you add some routes to your application configuration as well
to point to these actions.

::

    'routes': {
        'login': {
            'path': '/login',
            'options': {'controller': 'controllers.Public'},
            'defaults': {'action': 'login'}
        },
        'logout': {
            'path': '/logout',
            'options': {'controller': 'controllers.Public'},
            'defaults': {'action': 'logout'}
        }
    }

Anytime a user visits the **/login**, if the request is a POST (this can
be overridden if required) then the user with be authenticated. If they
visit **/logout** they they will be logged out and redirected to
``redirect_url``. If ``redirect_url`` is omitted, then the logout view
will be rendered.

Once the user has been autheticated, you can retrieve the user within
the controller by using \`self.request.

Authorization
~~~~~~~~~~~~~

watson-auth provides a strongly customizable authorization system. It
allows you to configure both roles, and permissions for users. The
management of these however is not controlled by watson-auth, so it will
be up to you to create the necessary UI to create/delete/update roles.

Defining the roles and permissions
''''''''''''''''''''''''''''''''''

First, define some roles for the system and add them to the session:

::

    from watson.auth import models

    role_regular = models.Role(name='Regular')
    role_admin = models.Role(name='Admin')

    session.add(role_regular)
    session.add(role_admin)

Next, define some permissions:

::

    permission_create = models.Permission(name='Create', key='create')
    permission_delete = models.Permission(name='Delete', key='delete')
    permission_read = models.Permission(name='Read', key='read')

    session.add(permission_create)
    session.add(permission_delete)
    session.add(permission_read)

Associate the permissions with the roles:

::

    role_admin.add_permission(permission_create)
    role_admin.add_permission(permission_read)
    role_admin.add_permission(permission_delete)

    role_regular.add_permission(permission_create)
    role_regular.add_permission(permission_read)

Finally, commit them to the database:

::

    session.commit()

Creating a new user
'''''''''''''''''''

watson-auth provides a base user mixin that has some common fields, and
should be subclassed. watson.auth.models.Model will be the declarative
base of whatever session you have configured in
config['auth']['db']['session'].

::

    from watson.auth import models
    from watson.form import fields

    class User(models.UserMixin, models.Model):
        __tablename__ = 'users'
        username = Column(String(255), unique=True)

Next, create the user and give them some roles and permissions:

::

    user = User(username='username', password='some password')
    session.add(user)

    user.roles.append(role_admin)

    session.commit()

If no permissions are specified, then the user will receive inherited
permissions from that role. Permissions can be given either allow (1) or
deny (0).

::

    user.add_permission(permission_create, value=0)

Authorizing your controllers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Like authentication, authorizing your controllers is done via
decorators.

::

    from watson.auth.decorators import auth
    from watson.framework import controllers

    class Public(controllers.Action):

        @auth
        def protected_action(self):
            # some sensitive page

``@auth`` also accepts the following arguments:

-  roles: A string or tuple containing the roles the user must have
-  permissions: A string or tuple containing the permissions the user
   must have
-  unauthenticated\_url: The url (or named route) to redirect to if the
   user isn't authenticated. By default this will be
   config['auth']['url']['unauthenticated']
-  unauthorized\_url: The url (or named route) to redirect to if the
   user isn't authorized. By default this will be
   config['auth']['url']['unauthorized']
-  should\_404: Boolean whether or not to raise a 404 instead of
   redirecting.

Accessing the user
~~~~~~~~~~~~~~~~~~

At any time within your controller you can access the user that's
currently authenticated through the request.

::

    class MyController(controllers.Action):
        def index_action(self):
            user = self.request.user
