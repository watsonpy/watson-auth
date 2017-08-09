import abc
from sqlalchemy.orm import exc
from watson.auth import crypto
from watson.auth.providers import exceptions
from watson.common import imports
from watson.common.decorators import cached_property


class Base(object):

    config = None
    session = None

    def __init__(self, config, session):
        self._validate_configuration(config)
        self.config = config
        self.session = session

    # Configuration

    def _validate_configuration(self, config):
        if 'class' not in config['model']:
            raise exceptions.InvalidConfiguration(
                'User model not specified, ensure "class" key is set on provider["model"].')
        common_keys = [
            'system_email_from_address',
            'reset_password_route',
            'forgotten_password_route']
        for key in common_keys:
            if key not in config:
                raise exceptions.InvalidConfiguration(
                    'Ensure "{}" key is set on the provider.'.format(key))

    # User retrieval

    @property
    def user_model_identifier(self):
        return self.config['model']['identifier']

    @cached_property
    def user_model(self):
        return imports.load_definition_from_string(
            self.config['model']['class'])

    @property
    def user_query(self):
        return self.session.query(self.user_model)

    def get_user(self, username):
        """Retrieves a user from the database based on their username.

        Args:
            username (string): The username of the user to find.
        """
        user_field = getattr(self.user_model, self.user_model_identifier)
        try:
            return self.user_query.filter(user_field == username).one()
        except exc.NoResultFound:
            return None

    def get_user_by_email_address(self, email_address):
        email_column = getattr(
            self.user_model, self.config['model']['email_address'])
        try:
            return self.user_query.filter(email_column == email_address).one()
        except exc.NoResultFound:
            return None

    # Authentication

    def authenticate(self, username, password):
        """Validate a user against a supplied username and password.

        Args:
            username (string): The username of the user.
            password (string): The password of the user.
        """
        password_config = self.config['password']
        if len(password) > password_config['max_length']:
            return None
        user = self.get_user(username)
        if user:
            if crypto.check_password(password, user.password, user.salt,
                                     self.config['encoding']):
                return user
        return None

    def user_meets_requirements(self, user, requires):
        for require in requires or []:
            if not require(user):
                return False
        return True

    # Authorization

    def is_authorized(self, user, roles=None, permissions=None, requires=None):
        no_role = roles and not user.acl.has_role(roles)
        no_permission = permissions and not user.acl.has_permission(
            permissions)
        no_requires = self.user_meets_requirements(user, requires)
        return False if no_role or no_permission or not no_requires else True

    # Actions

    @abc.abstractmethod
    def logout(self, request):
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def login(self, user, request):
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def handle_request(self, request):
        raise NotImplementedError  # pragma: no cover
