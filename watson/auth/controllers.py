# -*- coding: utf-8 -*-
from watson.framework import controllers
from watson.auth.decorators import login, logout, forgotten, reset


class Auth(controllers.Action):
    @login
    def login_action(self, form):
        return {'form': form}

    @logout
    def logout_action(self):
        pass

    @forgotten
    def forgotten_password_action(self, form):
        return {
            'form': form
        }

    @reset
    def reset_password_action(self, form):
        return {
            'form': form
        }
