# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.filter
def get_item(obj, key):
    return obj[key]

