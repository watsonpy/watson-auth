# -*- coding: utf-8 -*-

defaults = {
    'common': {
        'model': {
            'identifier': 'username',
            'email_address': 'username'
        },
        'session': 'default',
        'key': 'watson.user',
        'encoding': 'utf-8',
        'password': {
            'max_length': 30
        },
    },
    'default_provider': 'watson.auth.providers.Session',
    'providers': {}
}

templates = {
    '401': 'errors/401',
    '403': 'errors/403',
}
