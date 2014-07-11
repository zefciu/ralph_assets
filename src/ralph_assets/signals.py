#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Asset signal module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django.dispatch

post_transition = django.dispatch.Signal(['user', 'assets'])


@django.dispatch.receiver(post_transition)
def post_transition_handler(sender, user, assets, **kwargs):
    print(user)
    print(assets)
    print('generating_doc')
