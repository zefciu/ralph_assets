# -*- coding: utf-8 -*-
"""Support module models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lck.django.choices import Choices
from lck.django.common.models import Named
from ralph_assets import models_assets
from ralph_assets.models_assets import (
    AssetType,
    Asset,
    AssetOwner,
    ASSET_TYPE2MODE,
)


class SupportStatus(Choices):
    _ = Choices.Choice

    SUPPORT = Choices.Group(0)
    new = _("new")
    in_progress = _("in progress")
    waiting_for_release = _("waiting for release")
    used = _("used")
    loan = _("loan")
    damaged = _("damaged")
    liquidated = _("liquidated")
    in_service = _("in service")
    in_repair = _("in repair")
    ok = _("ok")


class Support(
    Named,
    models_assets.SupportAndAsset,
):
    contract_id = models.CharField(max_length=50, unique=True, blank=False)
    description = models.CharField(max_length=100, blank=True)
    attachments = models.ManyToManyField(
        models_assets.Attachment, null=True, blank=True
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True,
    )
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=False, blank=False)
    escalation_path = models.CharField(max_length=200, blank=True)
    contract_terms = models.CharField(max_length=200, blank=True)
    additional_notes = models.CharField(max_length=200, blank=True)
    sla_type = models.CharField(max_length=200, blank=True)
    asset_type = models.PositiveSmallIntegerField(
        choices=AssetType()
    )
    status = models.PositiveSmallIntegerField(
        default=SupportStatus.new.id,
        verbose_name=_("status"),
        choices=SupportStatus(),
        null=True,
        blank=True,
    )
    producer = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=100, blank=True)
    serial_no = models.CharField(max_length=100, blank=True)
    invoice_no = models.CharField(max_length=100, blank=True, db_index=True)
    invoice_date = models.DateField(null=True, blank=True, verbose_name=_('Invoice date'))
    period_in_months = models.IntegerField(null=True, blank=True)
    property_of = models.ForeignKey(
        AssetOwner,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    # TODO type
    assets = models.ManyToManyField(Asset)

    @property
    def url(self):
        return reverse('edit_support', kwargs={
            'support_id': self.id,
            'mode': ASSET_TYPE2MODE[self.asset_type],
        })
