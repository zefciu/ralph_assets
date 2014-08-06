# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from factory import (
    Sequence,
    lazy_attribute,
)
from factory.django import DjangoModelFactory

from django.contrib.auth.models import User
from django.test.client import Client


def login_as_user(user=None, password='ralph', *args, **kwargs):
    if not user:
        user = UserFactory(*args, **kwargs)
        user.set_password(password)
        user.save()
    client = Client()
    client.login(username=user.username, password=password)
    return client


class UserFactory(DjangoModelFactory):
    """
    User *password* is 'ralph'.
    """
    FACTORY_FOR = User

    username = Sequence(lambda n: 'user_%d' % n)

    @lazy_attribute
    def email(self):
        return '%s@example.com' % self.username

    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.set_password('ralph')
        user.save()
        return user


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True


class MessagesTestMixin(object):
    def assertMessageEqual(self, response, text):
        """
        Asserts that the response includes the message text.
        """
        messages = [m.message for m in response.context['messages']]
        if text not in messages:
            self.fail(
                'No message with text "{}", messages were: {}'.format(
                    text, messages,
                )
            )

from functools import partial


class AjaxClient(Client):
    """
    Dirty add methods: ajax_get, ajax_post, ajax_put, ajax_delete.
    """
    def __getattribute__(self, name):
        methods = ['get', 'post', 'put', 'delete']
        if name in ['ajax_{}'.format(method) for method in methods]:
            func_name = name.split('_')[1]
            func = super(AjaxClient, self).__getattribute__(func_name)
            return partial(func, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        else:
            return super(AjaxClient, self).__getattribute__(name)


class ClientMixin(object):

    def setUp(self):
        self.client = AjaxClient()
        super(ClientMixin, self).setUp()

    def login_as_user(self, user=None, password='ralph', *args, **kwargs):
        if not user:
            user = UserFactory(*args, **kwargs)
            user.set_password(password)
            user.save()
        self.client.login(username=user.username, password=password)

    def login_as_superuser(self):
        self.login_as_user(AdminFactory())
