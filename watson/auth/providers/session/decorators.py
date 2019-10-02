# -*- coding: utf-8 -*-
from urllib import parse
from watson.common import imports
from watson.framework import exceptions

DEPENDENCY = 'watson.auth.providers.Session'


def login(
        func=None,
        method='POST',
        redirect='/',
        redirect_callback=None,
        requires=None,
        invalid_credentials_message='Invalid username and/or password.',
        form_class='watson.auth.forms.Login'):
    """Attempts to log in a user based upon their supplied credentials.

    Args:
        method (string): The HTTP method that will trigger the authentication
        redirect (string): The URL/route that the user is redirected to if authenticated
        redirect_callback (callable): A callable that allows you to dynamically change where the user is redirected to
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
            redirect_url = provider.config.get('authenticated_route', redirect)
            if self.request.user:
                return self.redirect(redirect_url)
            form = imports.load_definition_from_string(
                form_class)(action=self.request)
            form.data = self.request
            user = None
            if self.request.is_method(method):
                if form.is_valid():
                    user = provider.authenticate(
                        username=getattr(form, provider.user_model_identifier),
                        password=form.password)
                if user:
                    if self.request.get['redirect']:
                        redirect_url = parse.unquote_plus(
                            self.request.get['redirect'])
                    if provider.user_meets_requirements(user, requires):
                        provider.login(user, self.request)
                        if redirect_callback:
                            redirect_url = redirect_callback(user)
                else:
                    self.flash_messages.add(
                        invalid_credentials_message, namespace='error')
                    redirect_url = form.action
                return self.redirect(redirect_url, clear=True)
            kwargs['form'] = form
            return func(self, **kwargs)
        return wrapper
    return decorator(func) if func else decorator


def logout(func=None, redirect=None):
    """Attempts to log a user out of the application.

    Args:
        redirect (string): The url to redirect to (or route)

    Example:

    .. code-block:: python

        class MyController(controllers.Action):
            @logout(redirect='home')
            def logout_action(self):
                pass
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider = self.container.get(DEPENDENCY)
            func(self, **kwargs)
            provider.logout(self.request)
            return self.redirect(redirect, clear=True)
        return wrapper
    return decorator(func) if func else decorator


def auth(
        func=None,
        roles=None,
        permissions=None,
        requires=None,
        login_redirect=None,
        should_remember_referrer=True):
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
            if not user:
                redirect_to = login_redirect if login_redirect else provider.config.get('login_route')
                if should_remember_referrer and redirect_to:
                    redirect_to = '{}?redirect={}'.format(
                        self.url(redirect_to),
                        parse.quote_plus(str(self.request.url)))
                if redirect_to:
                    return self.redirect(redirect_to)
                raise exceptions.ApplicationError(
                    status_code='403',
                    message='You must be logged in to view this page.')
            else:
                if not provider.is_authorized(
                        user, roles, permissions, requires):
                    raise exceptions.ApplicationError(
                        status_code='401',
                        message='You must be logged in to view this page.')
            return func(self, **kwargs)
        return wrapper

    return decorator(func) if func else decorator


def forgotten(
        func=None,
        method='POST',
        redirect='/',
        subject='A password reset request has been made',
        template='auth/emails/forgotten-password',
        success_message='A password reset request has been sent to your email.',
        error_message='Could not find your account in the system, please try again.',
        form_class='watson.auth.forms.ForgottenPassword'):
    """Finds a user and sends them a reset password request email.

    Args:
        method (string): The HTTP method that request must match.
        form_class (string): The qualified class name of the form.
        redirect (string): The URL/route to redirect to if the user is already authenticated
        subject (string): The subject line of the email
        template (string): The template for the email
        success_message (string): The flash message that will be displayed to the user if it's successful
        error_message (string): The flash message that will be displayed to the user if it fails
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider = self.container.get(DEPENDENCY)
            redirect_url = provider.config.get('authenticated_route', redirect)
            if self.request.user:
                return self.redirect(redirect_url)
            form = imports.load_definition_from_string(
                form_class)(action=self.request)
            if self.request.is_method(method):
                user = None
                namespace = 'error'
                message = error_message
                form.data = self.request
                if form.is_valid():
                    forgotten_password_token_manager = self.container.get(
                        'auth_forgotten_password_token_manager')
                    forgotten_password_token_manager.provider = provider
                    email_address = getattr(form, provider.config['model']['identifier'])
                    user = provider.get_user_by_email_address(email_address)
                if user:
                    namespace = 'success'
                    message = success_message
                    token = forgotten_password_token_manager.create_token(
                        user, self.request)
                    forgotten_password_token_manager.notify_user(
                        user,
                        request=self.request,
                        subject=subject,
                        template=template,
                        token=token)
                self.flash_messages.add(message, namespace)
                return self.redirect(str(self.request.url))
            kwargs['form'] = form
            return func(self, **kwargs)
        return wrapper

    return decorator(func) if func else decorator


def reset(
        func=None,
        method='POST',
        redirect='/',
        authenticate_on_reset=True,
        subject='Your password has been reset',
        template='auth/emails/reset-password',
        success_message='Your password has been changed successfully.',
        error_message='Could not find your account in the system, please try again.',
        invalid_message='The supplied passwords do not match, please try again.',
        form_class='watson.auth.forms.ResetPassword'):
    """Resets a users password if the token matches.

    If a token is not matched the user is redirected to the specified route/URL.

    Args:
        method (string): The HTTP method that request must match
        form_class (string): The qualified class name of the form
        authenticate_on_reset (boolean): Automatically log the user in on success
        redirect (string): The URL/route to redirect to if the user is already authenticated
        subject (string): The subject line of the email
        template (string): The template for the email
        success_message (string): The flash message that will be displayed to the user if it's successful
        error_message (string): The flash message that will be displayed to the user if it fails
        invalid_message (string): The flash message that will be displayed to the user if it fails due to a password mismatch
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider = self.container.get(DEPENDENCY)
            redirect_url = provider.config.get('authenticated_route', redirect)
            if self.request.user:
                return self.redirect(redirect_url)
            form = imports.load_definition_from_string(
                form_class)(action=self.request)
            kwargs['form'] = form
            forgotten_password_token_manager = self.container.get(
                'auth_forgotten_password_token_manager')
            forgotten_password_token_manager.provider = provider
            token = forgotten_password_token_manager.get_token(
                self.request.get['token'])
            namespace = 'error'
            message = error_message
            if self.request.is_method(method):
                form.data = self.request
                redirect_url = str(self.request.url)
                if form.is_valid():
                    if token:
                        message = success_message
                        namespace = 'success'
                        forgotten_password_token_manager.update_user_password(
                            token, form.password)
                        forgotten_password_token_manager.notify_user(
                            token.user,
                            request=self.request,
                            subject=subject,
                            template=template,
                            password=form.password)
                        if authenticate_on_reset:
                            provider.login(token.user, self.request)
                else:
                    message = invalid_message
                self.flash_messages.add(message, namespace)
                return self.redirect(redirect_url, clear=True)
            if not token:
                self.flash_messages.add(message, namespace)
                return self.redirect(
                    provider.config['forgotten_password_route'])
            return func(self, **kwargs)
        return wrapper

    return decorator(func) if func else decorator
