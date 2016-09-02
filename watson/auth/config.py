# -*- coding: utf-8 -*-

defaults = {
    'model': {
        'columns': {
            'username': 'username',
            'email': 'email'
        }
    },
    'authenticator': {
        'session': 'default',
        'password': {
            'max_length': 30,
            'encoding': 'utf-8'
        },
        'urls': {
            'unauthenticated': 'login',
            'unauthorized': 'unauthorized',
        }
    },
    'login': {
        'redirect_to_unauthenticated': False,
        'urls': {
            'success': '/',
            'route': 'login'
        },
        'form': {
            'class': 'watson.auth.forms.Login',
            'username_field': 'username',
            'password': 'password',
            'messages': {
                'invalid': 'Invalid username and/or password.'
            }
        }
    },
    'logout': {
        'urls': {
            'success': '/',
            'route': 'logout'
        }
    },
    'forgotten_password': {
        'urls': {
            'route': 'forgotten-password'
        },
        'subject_line': 'A password reset request has been made',
        'form': {
            'class': 'watson.auth.forms.ForgottenPassword',
            'username_field': 'username',
            'messages': {
                'success': 'A password reset request has been sent to your email.',
                'invalid': 'Could not find your account in the system, please try again.',
            }
        }
    },
    'reset_password': {
        'authenticate_on_reset': False,
        'urls': {
            'route': 'reset-password',
            'success': '/',
            'invalid': '/'
        },
        'form': {
            'class': 'watson.auth.forms.ResetPassword',
            'username_field': 'username',
            'messages': {
                'success': 'Your password has been changed successfully.',
                'invalid': 'Could not find your account in the system, please try again.',
            }
        }
    },
    'session': {
        'key': 'watson.user'
    },
}


definitions = {
    'auth_authenticator': {
        'item': 'watson.auth.authentication.Authenticator',
        'init': {
            'config': lambda container: container.get('application.config')['auth']['authenticator'],
            'session': lambda container: container.get('sqlalchemy_session_{0}'.format(container.get('application.config')['auth']['authenticator']['session'])),
            'user_model': lambda container: container.get('application.config')['auth']['model']['class'],
            'user_id_field': lambda container: container.get('application.config')['auth']['model']['columns']['username']
        },
    },
    'auth_forgotten_password_token_manager': {
        'item': 'watson.auth.authentication.ForgottenPasswordTokenManager',
        'init': {
            'config': lambda container: container.get('application.config')['auth']['forgotten_password'],
            'session': lambda container: container.get('sqlalchemy_session_{0}'.format(container.get('application.config')['auth']['authenticator']['session'])),
            'email_field': lambda container: container.get('application.config')['auth']['model']['columns']['email'],
            'mailer': lambda container: container.get('mailer')
        },
    }
}
