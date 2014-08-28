# -*- coding: utf-8 -*-
"""Templatetags specific for ralph_assets"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template
from django.utils.translation import ugettext_lazy as _

from ralph_assets.history.models import History


register = template.Library()


@register.inclusion_tag('assets/templatetags/short_history.html')
def short_history(obj, limit=5, full_history_button=True):
    """Render a short history table."""
    status_history = History.objects.get_history_for_this_object(
        obj=obj
    ).order_by('-date')
    return {
        'full_history_button': full_history_button,
        'history_for_model_url': History.get_history_url_for_object(obj),
        'history_title': _('Short history'),
        'limit': limit,
        'obj': obj,
        'status_history': status_history[:limit] if status_history else None,
    }


@register.inclusion_tag('assets/templatetags/short_history.html')
def status_history(obj, limit=5, full_history_button=True):
    """Render a short history table only for status changes."""
    status_history = History.objects.get_history_for_this_object(
        obj=obj
    ).filter(
        field_name__exact='status',
    ).order_by('-date')
    return {
        'full_history_button': full_history_button,
        'history_for_model_url': History.get_history_url_for_object(obj),
        'history_title': _('Status history'),
        'limit': limit,
        'obj': obj,
        'status_history': status_history[:limit] if status_history else None,
    }
