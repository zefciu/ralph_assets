# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select.fields import AutoCompleteSelectField
from django.forms import Form
from ralph_assets.forms import LOOKUPS


class TransitionForm(Form):
    user = AutoCompleteSelectField(
        LOOKUPS['asset_user'],
        required=True,
    )
    warehouse = AutoCompleteSelectField(
        LOOKUPS['asset_warehouse'],
        required=True,
    )
