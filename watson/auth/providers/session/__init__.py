from watson.auth.providers import abc


class Provider(abc.Base):

    defaults = {}

    def _validate_configuration(self, config):
        super(Provider, self)._validate_configuration(config)

    def handle_request(self, request):
        if not hasattr(request, 'user'):
            request.user = None
        if not request.user:
            request.user = None
            username = request.session[self.config['key']]
            if username:
                request.user = self.get_user(username)

    def login(self, user, request):
        request.user = user
        request.session[self.config['key']] = getattr(
            user, self.user_model_identifier)

    def logout(self, request):
        del request.session[self.config['key']]
        request.user = None
