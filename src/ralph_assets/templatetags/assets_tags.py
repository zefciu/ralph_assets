# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.inclusion_tag('assets/templatetags/transition_history.html')
def transition_history(asset):
    transitions_history = None
    if hasattr(asset, 'transitionshistory_set'):
        transitions_history = asset.transitionshistory_set.all()
    return {'transitions_history': transitions_history}
