# -*- coding: utf-8 -*-
import bcrypt
import uuid
from watson.auth import models
from watson.common import imports, decorators
from watson.db.contextmanagers import transaction_scope
from sqlalchemy.orm import exc


def generate_password(password, rounds=10, encoding='utf-8'):
    """Generate a new password based on a random salt.

    Args:
        password (string): The password to generate the hash off
        rounds (int): The complexity of the hashing

    Returns:
        mixed: The generated password and the salt used
    """
    salt = bcrypt.gensalt(rounds)
    return bcrypt.hashpw(password.encode(encoding), salt), salt


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
    return bcrypt.hashpw(password.encode(encoding), salt) == existing_password


def generate_forgotten_token():
    """Generates a unique identifier that can be used to validate a forgotten
    password request.
    """
    return uuid.uuid4().hex


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
    _config = None

    def __init__(self, config, session, user_model, user_id_field):
        self._config = config
        self.session = session
        self.user_model = user_model
        self.user_id_field = user_id_field

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
            user = self.user_query.filter(user_field == username).one()
        except exc.NoResultFound:
            return None
        return user

    def get_user_by_id(self, id):
        """Retrieves a user from the database based on their id.

        Args:
            id (int): The id of the user to find.
        """
        try:
            user = self.user_query.filter_by(id=id).one()
        except exc.NoResultFound:
            return None
        return user

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


class ForgottenPasswordTokenManager(object):
    """Manages a users forgotten password.

    Attributes:
        email_field (string): The email property of the user model.
        mailer (watson.mail.backends.abc.Base): The mailer backend used to send the email.
    """
    email_field = None
    mailer = None
    _config = None

    def __init__(self, config, session, mailer, email_field):
        self._config = config
        self.session = session
        self.mailer = mailer
        self.email_field = email_field

    def create_token(self, user, request):
        """Create a new forgotten password token.

        Email the user their reset password link. The template for this email
        can be overridden via `auth/emails/forgotten-password.html`.

        Args:
            user (watson.auth.models.User): The user who forgot their password
            request (watson.http.messages.Request): The HTTP request
        """
        token = models.ForgottenPasswordToken(token=generate_forgotten_token())
        user.forgotten_password_tokens.append(token)
        with transaction_scope(self.session) as session:
            session.add(user)
        self.mailer.send(
            subject=self._config['subject_line'],
            from_=self._config['from'],
            template='auth/emails/forgotten-password',
            body={'user': user, 'token': token, 'request': request},
            to=getattr(user, self.email_field))
        return token

    def get_token(self, token, model=models.ForgottenPasswordToken):
        """Retrieve a user based on the supplied token.

        Args:
            token (string): The forgotten password token
        """
        return self.session.query(
            model).filter_by(
                token=token).order_by(model.id.desc()).first()

    def update_user_password(self, token, password):
        """Update the users password.

        Once the user has been updated, make sure that the token has been
        deleted to prevent further access of that token.
        """
        token.user.password = password
        with transaction_scope(self.session) as session:
            session.add(token.user)
            session.delete(token)
