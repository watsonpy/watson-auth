# -*- coding: utf-8 -*-
from watson.common import imports
from watson.framework.views import Model


DEPENDENCY = 'watson.auth.providers.JWT'


def login(
        func=None,
        method='POST',
        requires=None,
        form_class='watson.auth.forms.Login'):
    """Attempts to log in a user based upon their supplied credentials.

    Args:
        method (string): The HTTP method that will trigger the authentication
        requires (list): A list of watson.validators.abc.Validator objects with which to validate the user against
        form_class (string): The form used to validate the user credentials against

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
            @login(redirect='home')
            def login_action(self):
                pass
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider = self.container.get(DEPENDENCY)
            form = imports.load_definition_from_string(
                form_class)(action=self.request)
            form.data = self.request
            user = None
            if self.request.is_method(method):
                result = {}
                if form.is_valid():
                    user = provider.authenticate(
                        username=getattr(form, provider.user_model_identifier),
                        password=form.password)
                if user and provider.user_meets_requirements(user, requires):
                    result['token'] = provider.login(user, self.request)
                else:
                    self.response.status_code = 403
                    result['message'] = 'Unable to authenticate the specified credentials.'
                return Model(format='json', data=result)
            return func(self, **kwargs)
        return wrapper
    return decorator(func) if func else decorator


def logout(func=None):
    """Attempts to log a user out of the application.

    Returns a new token for the application to use.

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
            @logout
            def logout_action(self):
                pass
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider = self.container.get(DEPENDENCY)
            func(self, **kwargs)
            return Model(
                format='json', data={'token': provider.logout(self.request)})
        return wrapper
    return decorator(func) if func else decorator


def auth(func=None, roles=None, permissions=None, requires=None):
    """Guards a controller action against unauthorized and unauthenticated access.

    Args:
        roles (list|string): A list of roles that are able to access the route
        permissions (list|string): A list of permissions that are able to access the route
        requires (list): A list of watson.validators.abc.Validator objects with which to validate the user against
        login_redirect (string): A URL/route to redirect the user to if they are unauthenticated
        should_remember_referrer (boolean): Whether or not

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
            @auth(roles='admin')
            def dashboard_action(self):
                pass
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider = self.container.get(DEPENDENCY)
            user = self.request.user
            status_code = 200
            if not user:
                status_code = 403
            else:
                if not provider.is_authorized(
                        user, roles, permissions, requires):
                    status_code = 401
            if status_code != 200:
                self.response.status_code = status_code
                return self.response
            return func(self, **kwargs)
        return wrapper

    return decorator(func) if func else decorator


def forgotten(
        func=None,
        method='POST',
        form_class='watson.auth.forms.ForgottenPassword'):
    """Finds a user and sends them a reset password request email.

    Args:
        method (string): The HTTP method that request must match.
        form_class (string): The qualified class name of the form.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            return func(self, **kwargs)
        return wrapper

    return decorator(func) if func else decorator


def reset(
        func=None,
        method='POST',
        authenticated_on_reset=False,
        form_class='watson.auth.forms.ForgottenPassword'):
    """Resets a users password if the token matches.

    If a token is not matched the user is redirected to the specified route/URL.

    Args:
        method (string): The HTTP method that request must match.
        authenticate_on_reset (boolean): Automatically log the user in on success.
        form_class (string): The qualified class name of the form.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            return func(self, **kwargs)
        return wrapper

    return decorator(func) if func else decorator
