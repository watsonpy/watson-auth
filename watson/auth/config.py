# -*- coding: utf-8 -*-

defaults = {
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
        'max_length': 30,
        'encoding': 'utf-8'
    }
}


definitions = {
    'auth_authenticator': {
        'item': 'watson.auth.authentication.Authenticator',
        'init': {
            'config': lambda container: container.get('application.config').get('auth', {})
        },
        'property': {
            'session': lambda container: container.get('sqlalchemy_session_{0}'.format(container.get('application.config')['auth']['db']['session'])),
            'user_model': lambda container: container.get('application.config')['auth']['db']['user_model'],
            'user_id_field': lambda container: container.get('application.config')['auth']['db']['username_field']
        }
    }
}
