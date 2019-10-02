# -*- coding: utf-8 -*-
from watson.common import datastructures, imports
from watson.console.command import find_commands_in_module
from watson.di import ContainerAware
from watson.framework import events
from watson.auth import config, commands


class Init(ContainerAware):

    """Bootstraps watson.auth into the event system of watson.
    """

    def __call__(self, event):
        self.ensure_database_initialised(event)
        self.update_config(event.target)
        self.setup_providers(event.target)
        self.setup_forgotten_password_manager(event.target)
        self.load_default_commands(event.target.config)
        self.setup_route_listener()

    def ensure_database_initialised(self, event):
        app_config = event.target.config
        event_name = 'watson.db.listeners.Init'
        db_listener = (event_name, 1, False)
        if db_listener not in app_config['events'][events.INIT]:
            listener = self.container.get(event_name)
            listener(event)

    def load_default_commands(self, config):
        existing_commands = config.get('commands', [])
        db_commands = find_commands_in_module(commands)
        db_commands.extend(existing_commands)
        config['commands'] = db_commands

    def update_config(self, app):
        app.config['auth'] = datastructures.dict_deep_update(
            config.defaults, app.config.get('auth', {}))
        app.container.get('app_exception_listener').templates.update(
            config.templates)
        self.container.get('jinja2_renderer').add_package_loader(
            'watson.auth', 'views')

    def setup_providers(self, app):
        auth_config = app.config['auth']
        if not auth_config['providers']:
            auth_config['providers'][auth_config['default_provider']] = {}
        for provider, config_ in auth_config['providers'].items():
            self._setup_provider(app, provider, config_)

    def _setup_provider(self, app, provider, config_):
        auth_config = app.config['auth']
        provider_ = imports.load_definition_from_string(provider)
        provider_config = datastructures.dict_deep_update(
            auth_config['common'], provider_.defaults)
        provider_config = datastructures.dict_deep_update(
            provider_config, config_)
        config_.update(provider_config)
        dependency_config = {
            'init': {
                'config': lambda container: container.get('application.config')['auth']['providers'][provider],
                'session': lambda container: container.get('sqlalchemy_session_{0}'.format(container.get('application.config')['auth']['providers'][provider]['session'])),
            }
        }
        dependency_config.update(app.config['dependencies'][
            'definitions'].get(provider, {}))
        app.container.add_definition(provider, dependency_config)

    def setup_forgotten_password_manager(self, app):
        app.container.add_definition('auth_forgotten_password_token_manager', {
            'item': 'watson.auth.managers.ForgottenPasswordToken',
            'init': {
                'mailer': 'mailer',
                'email_address_field': app.config['auth']['common']['model']['email_address']
            }
        })

    def setup_route_listener(self):
        dispatcher = self.container.get('shared_event_dispatcher')
        dispatcher.add(
            events.ROUTE_MATCH,
            self.container.get('watson.auth.listeners.Route'),
            1,
            False)


class Route(ContainerAware):

    """Listens for a route event and attempts to inject the user into the
    request if one has been authenticated.
    """

    def __call__(self, event):
        auth_config = self.container.get('application').config['auth']
        request = event.params['context']['request']
        for provider in auth_config['providers']:
            provider = self.container.get(provider)
            provider.handle_request(request)
