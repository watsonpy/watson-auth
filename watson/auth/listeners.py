# -*- coding: utf-8 -*-
from watson.common import datastructures
from watson.di import ContainerAware
from watson.framework import applications, events
from watson.auth import config


class Init(ContainerAware):

    """Bootstraps watson.auth into the event system of watson.
    """

    @property
    def app_config(self):
        return self.container.get('application.config')

    def __call__(self, event):
        # Initialize watson.db if it hasn't been added to the app config
        db_listener = ('watson.db.listeners.Init', 1, True)
        if db_listener not in self.app_config['events']['event.mvc.init']:
            listener = self.container.get('watson.db.listeners.Init')
            listener(event)
        self.setup_config()
        self.setup_listeners()
        self.setup_authenticator()

    def setup_config(self):
        auth_config = datastructures.dict_deep_update(
            config.defaults, self.app_config.get('auth', {}))
        self.app_config['auth'] = auth_config

    def setup_authenticator(self):
        dependency_config = datastructures.dict_deep_update(
            config.definitions['auth_authenticator'], self.app_config['dependencies']['definitions'].get('auth_authenticator', {}))
        self.app_config['dependencies']['definitions']['auth_authenticator'] = dependency_config
        self.container.definitions['auth_authenticator'] = dependency_config

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
