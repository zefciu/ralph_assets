# -*- coding: utf-8 -*-
"""Forms for support module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.forms.widgets import Textarea

from ralph.ui.widgets import DateWidget
from ralph_assets import models_support


class SupportContractForm(forms.ModelForm):
    """SupportContract add/edit form for supports."""

    def __init__(self, mode, *args, **kwargs):
        self.mode = mode
        super(SupportContractForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        result = super(SupportContractForm, self).clean(*args, **kwargs)
        return result

    class Meta:
        model = models_support.SupportContract
        fields = (
            'contract_id',
            'name',
            'description',
            'attachment',
            'cost',
            'date_from',
            'date_to',
            'escalation_path',
            'contract_terms',
            'additional_notes',
            'sla_type',
        )
        widgets = {
            'date_from': DateWidget,
            'date_to': DateWidget,
            'description': Textarea(attrs={'rows': 5}),
            'escalation_path': Textarea(attrs={'rows': 5}),
            'contract_terms': Textarea(attrs={'rows': 5}),
            'additional_notes': Textarea(attrs={'rows': 5}),
            'sla_type': Textarea(attrs={'rows': 5}),
        }
