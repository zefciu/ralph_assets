# -*- coding: utf-8 -*-
"""Templatetags specific for ralph_assets"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template

from ralph_assets.models import url


register = template.Library()


@register.simple_tag
def get_edit_url(object_):
    """Returns the url of edit page for a given object (currently implemented
    for Users, expand if needed)
    """
    return url(object_)


@register.inclusion_tag('assets/templatetags/transition_history.html')
def transition_history(asset):
    transitions_history = None
    if hasattr(asset, 'transitionshistory_set'):
        transitions_history = asset.transitionshistory_set.all()
    return {'transitions_history': transitions_history}


@register.filter
def get_item(obj, key):
    return obj[key]
