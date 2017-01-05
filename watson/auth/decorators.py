# -*- coding: utf-8 -*-
from urllib import parse
from watson.common import imports
from watson.framework import exceptions


def auth(func=None, roles=None, permissions=None, requires=None,
         unauthenticated_url=None, unauthorized_url=None,
         should_404=False, redirect=False):
    """Makes a controller action require an authenticated user.

    By setting additional roles and permissions, finer control can be given
    to the resource.

    Args:
        func (callable): the function that is being wrapped
        roles (string|iterable): The roles that the user must have
        permissions (string|iterable): The permissions the user must have
        requires (iterable): An iterable of watson.validator.Validator objects
                             that allows for custom validations outside of
                             standard roles/permissions.
        unauthenticated_url (string): The url to redirect to if the user
                                      is not logged in.
        unauthorized_url (string): The url to redirect to if the user does
                                   not have permission.
        should_404 (boolean): Raise a 404 instead of redirecting.
        redirect (boolean): Remember the url to redirect to after login.

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
            config_urls = auth_config['authenticator']['urls']
            unauthent_url = unauthenticated_url or config_urls['unauthenticated']
            # User has not been authenticated
            if not user_id:
                if redirect or auth_config['login']['redirect_to_unauthenticated']:
                    unauthent_url = '{}?redirect={}'.format(
                        unauthent_url, parse.quote_plus(str(self.request.url)))
                return self.redirect(unauthent_url)
            authenticator = self.container.get('auth_authenticator')
            if not hasattr(self.request, 'user'):
                setattr(self.request, 'user', authenticator.get_user(user_id))
            user = self.request.user
            if not user:
                return self.redirect(unauthent_url)

            # User has been authenticated, but is not authorized
            unauthor_url = unauthorized_url or config_urls['unauthorized']
            no_role = roles and not user.acl.has_role(roles)
            no_permission = permissions and not user.acl.has_permission(
                permissions)
            no_require = False
            if requires:
                for require in requires:
                    if not require(self.request.user):
                        no_require = True
                        break
            if no_role or no_permission or no_require:
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
            login_config = auth_config['login']
            valid = True
            if self.request.user:
                # User is already authenticated, redirect to success url
                if auto_redirect:
                    return self.redirect(login_config['urls']['success'])
            form_config = login_config['form']
            form_class_module = form_class or form_config['class']
            form = imports.load_definition_from_string(form_class_module)(
                action=self.request)
            kwargs['form'] = form
            if self.request.is_method(method):
                # Form has been posted, validate the user
                form.data = self.request
                if form.is_valid():
                    authenticator = self.container.get('auth_authenticator')
                    username_field = getattr(form, form_config['username_field'])
                    password_field = getattr(form, form_config['password'])
                    user = authenticator.authenticate(
                        username=username_field,
                        password=password_field)
                    if user:
                        authenticator.assign_user_to_session(
                            user,
                            self.request,
                            auth_config['session']['key'])
                        if auto_redirect:
                            redirect_url = login_config['urls']['success']
                            if self.request.get['redirect']:
                                redirect_url = parse.unquote_plus(
                                    self.request.get['redirect'])
                            return self.redirect(redirect_url, clear=True)
                    else:
                        valid = False
                else:
                    valid = False
            if not valid:
                self.flash_messages.add(
                    form_config['messages']['invalid'], 'error')
                return self.redirect(login_config['urls']['route'])
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
            logout_config = auth_config['logout']
            del self.request.session[auth_config['session']['key']]
            redirect_to = logout_config['urls']['success']
            if redirect_url:
                redirect_to = redirect_url
            func(self, **kwargs)
            self.request.user = None
            return self.redirect(redirect_to)
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator


def forgotten(func=None, method='POST', form_class=None):
    """Finds a user and sends them a reset password request email.

    Args:
        func (callable): the function that is being wrapped.
        method (string): The HTTP method that request must match.
        form_class (string): The qualified class name of the form.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            auth_config = self.container.get('application').config['auth']
            forgotten_config = auth_config['forgotten_password']
            if hasattr(self.request, 'user') and self.request.user:
                # User is already authenticated, redirect to success url
                return self.redirect(auth_config['login']['urls']['success'])
            form_config = forgotten_config['form']
            form_class_module = form_class or form_config['class']
            form = imports.load_definition_from_string(form_class_module)(
                action=self.request)
            kwargs['form'] = form
            if self.request.is_method(method):
                form.data = self.request
                invalid = True
                if form.is_valid():
                    authenticator = self.container.get('auth_authenticator')
                    forgotten_password_token_manager = self.container.get(
                        'auth_forgotten_password_token_manager')
                    username_field = getattr(
                        form, form_config['username_field'])
                    user = authenticator.get_user_by_username_or_email(
                        username_field)
                    if user:
                        token = forgotten_password_token_manager.create_token(
                            user, self.request)
                        forgotten_password_token_manager.notify_user(
                            user,
                            request=self.request,
                            subject=auth_config['forgotten_password']['subject_line'],
                            template=auth_config['forgotten_password']['template'],
                            token=token)
                        invalid = False
                        self.flash_messages.add(
                            form_config['messages']['success'], 'success')
                        return self.redirect(str(self.request.url))
                if invalid:
                    self.flash_messages.add(
                        form_config['messages']['invalid'], 'error')
            return func(self, **kwargs)
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator


def reset(func=None, method='POST', form_class=None, authenticate_on_reset=False):
    """Resets a users password if the token matches.

    If a token is not matched the user is redirected to the specified route/url.

    Args:
        func (callable): the function that is being wrapped.
        method (string): The HTTP method that request must match.
        form_class (string): The qualified class name of the form.
        authenticate_on_reset (bool): Automatically log the user in on success.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            auth_config = self.container.get('application').config['auth']
            request = self.request
            if hasattr(request, 'user') and request.user:
                # User is already authenticated, redirect to success url
                return self.redirect(auth_config['login']['urls']['success'])
            reset_config = auth_config['reset_password']
            form_config = reset_config['form']
            form_class_module = form_class or form_config['class']
            form = imports.load_definition_from_string(form_class_module)(
                action=request)
            kwargs['form'] = form
            forgotten_password_token_manager = self.container.get(
                'auth_forgotten_password_token_manager')
            token = forgotten_password_token_manager.get_token(
                request.get['token'])
            if request.is_method(method) and token:
                authenticator = self.container.get('auth_authenticator')
                form.data = request
                if form.is_valid():
                    self.flash_messages.add(
                        form_config['messages']['success'], 'error')
                    redirect_url = reset_config['urls']['success']
                    auto_login = authenticate_on_reset or reset_config['authenticate_on_reset']
                    if auto_login:
                        authenticator.assign_user_to_session(
                            token.user,
                            request,
                            auth_config['session']['key'])
                        forgotten_password_token_manager.update_user_password(
                            token, form.password)
                        redirect_url = auth_config['login']['urls']['success']
                    forgotten_password_token_manager.notify_user(
                            token.user,
                            request=self.request,
                            subject=auth_config['reset_password']['subject_line'],
                            template=auth_config['reset_password']['template'],
                            password=form.password)
                    forgotten_password_token_manager.delete_token(token)
                    return self.redirect(redirect_url, clear=True)
                else:
                    self.flash_messages.add(
                        form_config['messages']['invalid_match'], 'error')
            if not token:
                self.flash_messages.add(
                    form_config['messages']['invalid'], 'error')
                return self.redirect(reset_config['urls']['invalid'])
            return func(self, **kwargs)
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator
