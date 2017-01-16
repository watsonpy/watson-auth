# -*- coding: utf-8 -*-
import uuid
from watson.auth import models
from watson.db.contextmanagers import transaction_scope


def generate_forgotten_token():
    """Generates a unique identifier that can be used to validate a forgotten
    password request.
    """
    return uuid.uuid4().hex


class ForgottenPasswordToken(object):
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
        return token

    def notify_user(self, user, request, subject, template, **kwargs):
        """Notify a user regarding a specific action via email.

        Args:
            user (watson.auth.models.User): The user to notify
            request (watson.http.messages.Request): The HTTP request
            subject (string): The subject of the email
            template (string): The html template to be used in the email
        """
        body = {'user': user, 'request': request}
        body.update(kwargs)
        self.mailer.send(
            subject=subject,
            from_=self._config['from'],
            template=template,
            body=body,
            to=getattr(user, self.email_field))

    def delete_token(self, token):
        """Delete a token.

        Args:
            token: The token identifier to be deleted
        """
        with transaction_scope(self.session) as session:
            session.delete(token)

    def get_token(self, token, model=models.ForgottenPasswordToken):
        """Retrieve a user based on the supplied token.

        Args:
            token (string): The forgotten password token identifier
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
