# -*- coding: utf-8 -*-
"""Forms for support module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select.fields import AutoCompleteSelectMultipleField
from collections import OrderedDict
from django_search_forms.fields import (
    DateRangeSearchField,
    TextSearchField,
)
from django import forms
from django.forms.widgets import Textarea
from django_search_forms.form import SearchForm

from ralph.ui.widgets import DateWidget
from ralph_assets import models_support
from ralph_assets.forms import LOOKUPS


class SupportForm(forms.ModelForm):
    """Support add/edit form for supports."""

    assets = AutoCompleteSelectMultipleField(
        LOOKUPS['asset'], required=False)

    class Meta:
        model = models_support.Support
        fieldset = OrderedDict([
            ('Info', [
                'asset_type', 'contract_id', 'name',
                'description', 'price', 'date_from',
                'date_to', 'escalation_path',
                'contract_terms', 'additional_notes',
                'sla_type', 'producer', 'supplier',
                'serial_no', 'invoice_no', 'invoice_date',
                'period_in_months', 'property_of', 'assets',
            ]),
        ])
        widgets = {
            'date_from': DateWidget,
            'date_to': DateWidget,
            'description': Textarea(attrs={'rows': 5}),
            'escalation_path': Textarea(attrs={'rows': 5}),
            'contract_terms': Textarea(attrs={'rows': 5}),
            'additional_notes': Textarea(attrs={'rows': 5}),
            'sla_type': Textarea(attrs={'rows': 5}),
            'invoice_date': DateWidget,
        }
        fields = (
            'asset_type',
            'contract_id',
            'name',
            'description',
            'price',
            'date_from',
            'date_to',
            'escalation_path',
            'contract_terms',
            'additional_notes',
            'sla_type',
            'producer',
            'supplier',
            'serial_no',
            'invoice_no',
            'invoice_date',
            'period_in_months',
            'property_of',
        )

    def __init__(self, mode, *args, **kwargs):
        self.mode = mode
        super(SupportForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        result = super(SupportForm, self).clean(*args, **kwargs)
        return result


class SupportSearchForm(SearchForm):
    class Meta(object):
        Model = models_support.Support
        fields = []
    contract_id = TextSearchField()
    name = TextSearchField()
    description = TextSearchField()
    date_from = DateRangeSearchField()
    date_to = DateRangeSearchField()
