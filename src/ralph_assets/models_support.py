# -*- coding: utf-8 -*-
"""Support module models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from lck.django.common.models import (
    Named,
)
from ralph_assets.models_assets import (AssetType, _get_file_path)


class SupportContract(Named):
    contract_id = models.CharField(max_length=50, unique=True, blank=False)
    description = models.CharField(max_length=100, blank=True)
    attachment = models.FileField(upload_to=_get_file_path, blank=True)
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    date_from = models.DateField(null=False, blank=False)
    date_to = models.DateField(null=False, blank=False)
    #notification_period ?
    escalation_path = models.CharField(max_length=200, blank=True)
    contract_terms = models.CharField(max_length=200, blank=True)
    additional_notes = models.CharField(max_length=200, blank=True)
    sla_type = models.CharField(max_length=200, blank=True)
    asset_type = models.PositiveSmallIntegerField(choices=AssetType())

    @property
    def url(self):
        return reverse('edit_support', kwargs={
            'support_id': self.id,
            'mode': {
                AssetType.data_center: 'dc',
                AssetType.back_office: 'back_office',
            }[self.asset_type],
        })
