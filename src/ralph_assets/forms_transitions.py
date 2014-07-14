# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select.fields import AutoCompleteSelectField
from dj.choices import Country
from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph_assets.forms import LOOKUPS, RALPH_DATE_FORMAT_LIST
from ralph.ui.widgets import DateWidget


class TransitionForm(forms.Form):
    user = AutoCompleteSelectField(
        LOOKUPS['asset_user'],
        required=True,
    )
    warehouse = AutoCompleteSelectField(
        LOOKUPS['asset_warehouse'],
        required=True,
    )
    loan_end_date = forms.DateField(
        required=True, widget=DateWidget(attrs={
            'class': 'end-date-field ',
            'placeholder': _('End YYYY-MM-DD'),
            'data-collapsed': True,
        }),
        label=_('Loan end date'),
        input_formats=RALPH_DATE_FORMAT_LIST,
    )
    country = forms.ChoiceField(
        choices=[('', '----')] + Country(),
        label=_('Country'),
        required=True,
    )
