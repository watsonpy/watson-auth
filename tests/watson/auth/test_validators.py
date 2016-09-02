# -*- coding: utf-8 -*-
from pytest import raises
from watson.auth.validators import Match
from tests.watson.auth import support


class TestMatchValidators(object):
    def test_valid_match(self):
        form = support.TestSampleForm()
        form.field_two = 'test'
        validator = Match('field_two')
        assert validator('test', form)

    def test_invalid_match(self):
        form = support.TestSampleForm()
        form.field_two = 'test2'
        validator = Match('field_two')
        with raises(ValueError):
            validator('test', form)


