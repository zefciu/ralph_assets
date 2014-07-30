# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from factory import Sequence, lazy_attribute
from factory.django import DjangoModelFactory

from django.contrib.auth.models import User


class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User

    username = Sequence(lambda n: 'user_%d' % n)

    @lazy_attribute
    def email(self):
        return '%s@example.com' % self.username


class AdminFactory(UserFactory):
    admin = True
