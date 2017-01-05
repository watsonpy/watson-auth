# -*- coding: utf-8 -*-
from watson.framework.debug import abc

data = []


class User(abc.Panel):
    title = 'Auth'
    icon = 'user'

    @property
    def request(self):
        return self.event.params['context']['request']

    @property
    def user(self):
        user = None
        if hasattr(self.request, 'user') and getattr(self.request, 'user'):
            user = getattr(
                getattr(self.request, 'user'),
                self.application.config['auth']['model']['columns']['username']
            )
        return user

    def render(self):
        return self._render({
            'request': self.request,
            'user': self.user
        })

    def render_key_stat(self):
        return self.user

