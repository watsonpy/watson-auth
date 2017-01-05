# -*- coding: utf-8 -*-
from watson.common import datastructures
from watson.console.command import find_commands_in_module
from watson.di import ContainerAware
from watson.framework import events
from watson.auth import config, commands


class Init(ContainerAware):

    """Bootstraps watson.auth into the event system of watson.
    """

    __ioc_definition__ = {
        'property': {
            'app_config': 'application.config',
        }
    }

    app_config = None

    def __call__(self, event):
        app = event.target
        self.setup_database(event)
        self.setup_config()
        self.load_default_commands(app.config)
        self.setup_listeners()
        self.setup_authenticator()

    def setup_database(self, event):
        # Initialize watson.db if it hasn't been added to the app config
        db_listener = ('watson.db.listeners.Init', 1, False)
        if db_listener not in self.app_config['events'][events.INIT]:
            listener = self.container.get('watson.db.listeners.Init')
            listener(event)

    def load_default_commands(self, config):
        """Load some existing
        """
        existing_commands = config.get('commands', [])
        db_commands = find_commands_in_module(commands)
        db_commands.extend(existing_commands)
        config['commands'] = db_commands

    def setup_config(self):
        auth_config = datastructures.dict_deep_update(
            config.defaults, self.app_config.get('auth', {}))
        self.app_config['auth'] = auth_config
        self.container.get('jinja2_renderer').add_package_loader(
            'watson.auth', 'views')

    def setup_authenticator(self):
        for name, definition in config.definitions.items():
            dependency_config = datastructures.dict_deep_update(
                config.definitions[name],
                self.app_config['dependencies']['definitions'].get(name, {}))
            self.app_config['dependencies']['definitions'][name] = dependency_config
            self.container.definitions[name] = dependency_config

    def setup_listeners(self):
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
        request.user = None
        user_id = request.session[auth_config['session']['key']]
        if user_id:
            authenticator = self.container.get('auth_authenticator')
            request.user = authenticator.get_user(user_id)
