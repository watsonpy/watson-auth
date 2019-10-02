import datetime
import jwt
from watson.auth.providers import abc, exceptions


class Provider(abc.Base):

    defaults = {
        'algorithm': 'HS256'
    }

    def _validate_configuration(self, config):
        super(Provider, self)._validate_configuration(config)
        if 'secret' not in config:
            raise exceptions.InvalidConfiguration(
                'Secret not specified, ensure "secret" key is set on provider configuration.')

    def _create_token(self, user, expiry=None):
        username = getattr(user, self.user_model_identifier)
        payload = {self.config['key']: username}
        expiry = self.config.get('expiry') or expiry
        if expiry:
            payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=expiry)
        return jwt.encode(
            payload,
            self.config['secret'],
            algorithm=self.config['algorithm']).decode(self.config['encoding'])

    def login(self, user, request):
        return self._create_token(user)

    def logout(self, request):
        request.user = None
        if request.user:
            return self._create_token(request.user, expiry=-1)
        return ''

    def handle_request(self, request):
        if not hasattr(request, 'user'):
            request.user = None
        if not request.user:
            authorization_header = request.headers.get('Authorization')
            request.user = None
            if authorization_header:
                token = authorization_header.split(' ')[1].encode(
                    self.config['encoding'])
                try:
                    payload = jwt.decode(
                        token,
                        self.config['secret'],
                        algorithms=[self.config['algorithm']])
                    username = payload[self.config['key']]
                    request.user = self.get_user(username)
                except:  # noqa, pragma: no cover
                    pass
