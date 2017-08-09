# -*- coding: utf-8 -*-
import bcrypt


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
    return bcrypt.hashpw(
        password.encode(encoding), salt) == existing_password
