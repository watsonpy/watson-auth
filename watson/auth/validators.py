# -*- coding: utf-8 -*-
from watson.validators import abc


class Match(abc.Validator):
    """Provides the ability to ensure two fields have the same value.
    """

    def __init__(self, field, message='Supplied value for "{field}" does not match.'):
        """Initial the validator.

        Args:
            field (str): The field name to match
        """
        self.message = message
        self.field = field

    def __call__(self, value, form):
        matching_field_value = getattr(form, self.field)
        if value != matching_field_value:
            raise ValueError(self.message.format(
                field=self.field))
        return True
