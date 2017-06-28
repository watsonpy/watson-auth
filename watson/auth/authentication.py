# -*- coding: utf-8 -*-
import bcrypt
from watson.common import imports, decorators
from sqlalchemy.orm import exc
from sqlalchemy import or_


def generate_password(password, rounds=10, encoding='utf-8'):
    """Generate a new password based on a random salt.

    Args:
        password (string): The password to generate the hash off
        rounds (int): The complexity of the hashing

    Returns:
        mixed: The generated password and the salt used
    """
    salt = bcrypt.gensalt(rounds)
    hashed_password = bcrypt.hashpw(password.encode(encoding), salt)
    return hashed_password.decode(encoding), salt.decode(encoding)


def check_password(password, existing_password, salt, encoding='utf-8'):
    """Validate a password against an existing password and the salt used to
    generate it.

    Args:
        password (string): The password to validate
        existing_password (string): The password to validate against
        salt (string): The salt used to generate the existing_password

    Returns:
        boolean: True/False if valid or invalid
    """
    if isinstance(salt, str):
        salt = salt.encode(encoding)
    if isinstance(existing_password, str):
        existing_password = existing_password.encode(encoding)
    return bcrypt.hashpw(password.encode(encoding), salt) == existing_password


class Authenticator(object):
    """Authenticates a user against the database.

    Attributes:
        session: The SqlAlchemy session to use.
        user_model (string): The class name of the user model.
        user_id_field (string): The field that is to be used as the username.
    """
    session = None
    user_model = None
    user_id_field = None
    email_field = None
    _config = None

    def __init__(
            self, config, session, user_model, user_id_field, email_field):
        self._config = config
        self.session = session
        self.user_model = user_model
        self.user_id_field = user_id_field
        self.email_field = email_field

    @decorators.cached_property
    def user_model_class(self):
        """The of the user_model to be used.
        """
        return imports.load_definition_from_string(self.user_model)

    @property
    def user_query(self):
        return self.session.query(self.user_model_class)

    def get_user(self, username):
        """Retrieves a user from the database based on their username.

        Args:
            username (string): The username of the user to find.
        """
        user_field = getattr(self.user_model_class, self.user_id_field)
        try:
            return self.user_query.filter(user_field == username).one()
        except exc.NoResultFound:
            return None

    def get_user_by_username_or_email(self, data):
        """Retrieves a user from the database based on their user or email.

        Args:
            data (string): The username/email of the user to find.
        """
        user_field = getattr(self.user_model_class, self.user_id_field)
        email_field = getattr(self.user_model_class, self.email_field)
        try:
            return self.user_query.filter(
                or_(user_field == data, email_field == data)).one()
        except exc.NoResultFound:
            return None

    def get_user_by_id(self, id):
        """Retrieves a user from the database based on their id.

        Args:
            id (int): The id of the user to find.
        """
        try:
            return self.user_query.filter_by(id=id).one()
        except exc.NoResultFound:
            return None

    def authenticate(self, username, password):
        """Validate a user against a supplied username and password.

        Args:
            username (string): The username of the user.
            password (string): The password of the user.
        """
        password_config = self._config['password']
        if len(password) > password_config['max_length']:
            return None
        user = self.get_user(username)
        if user:
            if check_password(password, user.password, user.salt,
                              password_config['encoding']):
                return user
        return None

    def assign_user_to_session(self, user, request, session_key):
        """Assign a user to the session.
        """
        request.user = user
        request.session[session_key] = getattr(
            user, self.user_id_field)
