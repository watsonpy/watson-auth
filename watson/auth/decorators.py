# -*- coding: utf-8 -*-
from watson.common import imports
from watson.framework import exceptions


def auth(func=None, roles=None, permissions=None,
         unauthenticated_url=None, unauthorized_url=None,
         should_404=False):
    """Makes a controller action require an authenticated user.

    By setting additional roles and permissions, finer control can be given
    to the resource.

    Args:
        func (callable): the function that is being wrapped
        roles (string|iterable): The roles that the user must have
        permissions (string|iterable): The permissions the user must have
        unauthenticated_url (string): The url to redirect to if the user
                                      is not logged in.
        unauthorized_url (string): The url to redirect to if the user does
                                   not have permission.
        should_404 (boolean): Raise a 404 instead of redirecting.

    Returns:
        The controller response.

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
            def index_action(self):
                return 'Index'

            @auth(roles='admin', permissions='view')
            def protected_action(self):
                return 'Authenticated users only'
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            auth_config = self.container.get('application.config')['auth']
            user_id = self.request.session[auth_config['session']['key']]
            unauthent_url = unauthenticated_url or auth_config['url'][
                'unauthenticated']
            # User has not been authenticated
            if not user_id:
                return self.redirect(unauthent_url)
            authenticator = self.container.get('auth_authenticator')
            if not hasattr(self.request, 'user'):
                setattr(self.request, 'user', authenticator.get_user(user_id))
            user = self.request.user
            if not user:
                return self.redirect(unauthent_url)

            # User has been authenticated, but is not authorized
            unauthor_url = unauthorized_url or auth_config[
                'url']['unauthorized']
            if (roles and not user.acl.has_role(roles)) or \
                    (permissions and not user.acl.has_permission(permissions)):
                if should_404:
                    raise exceptions.NotFoundError('Not found')
                return self.redirect(unauthor_url)

            # User is valid
            return func(self, **kwargs)
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator


def login(func=None, method='POST', form_class=None, auto_redirect=True):
    """Attempts to authenticate a user if the required fields have been posted.

    By setting auto_redirect to False, the user roles and permissions can be
    checked within the login route and redirected from there.

    Args:
        func (callable): the function that is being wrapped
        method (string): The HTTP method that authentication will be performed
                         against.
        form_class (string): The qualified class name of the form.
        auto_redirect (boolean): Whether or not to automatically redirect to a
                                 different url on successful login.

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
        @login(auto_redirect=False)
        def login_action(self):
            return 'Logged In'
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self.request, 'user'):
                self.request.user = None
            auth_config = self.container.get('application.config')['auth']
            valid = True
            if self.request.user:
                # User is already authenticated, redirect to success url
                if auto_redirect:
                    return self.redirect(auth_config['url']['login_success'])
            form_config = auth_config['form']
            if self.request.is_method(method):
                # Form has been posted, validate the user
                form_class_module = form_class or form_config['class']
                form = imports.load_definition_from_string(form_class_module)()
                form.data = self.request
                if form.is_valid():
                    authenticator = self.container.get('auth_authenticator')
                    username_field = getattr(form, form_config['username'])
                    password_field = getattr(form, form_config['password'])
                    user = authenticator.authenticate(
                        username=username_field,
                        password=password_field)
                    if user:
                        self.request.user = user
                        self.request.session[auth_config['session']['key']] = getattr(
                            user, auth_config['db']['username_field'])
                        if auto_redirect:
                            return (
                                self.redirect(
                                    auth_config['url']['login_success'])
                            )
                    else:
                        valid = False
                else:
                    valid = False
            if not valid:
                self.flash_messages.add(
                    form_config['invalid_message'], 'error')
                return self.redirect(auth_config['url']['login'])
            return func(self, **kwargs)
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator  # pragma: no cover


def logout(func=None, redirect_url=None):
    """Attempts to log a user out of the application.

    Args:
        redirect_url (string): The url to redirect to.

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
            def index_action(self):
                return 'Index'

            @logout(redirect_url='home')
            def logout_action(self):
                pass
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            auth_config = self.container.get('application').config['auth']
            del self.request.session[auth_config['session']['key']]
            self.request.user = None
            if redirect_url:
                return self.redirect(redirect_url)
            return func(self, **kwargs)
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator
