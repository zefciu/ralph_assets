# -*- coding: utf-8 -*-
"""Templatetags specific for ralph_assets"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


register = template.Library()

@register.simple_tag
def get_edit_url(o):
    """Returns the url of edit page for a given object (currently implemented
    for Users, expand if needed)
    """
    if isinstance(o, User):
        return reverse('edit_user', kwargs={'username': o.username})
