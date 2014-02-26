# -*- coding: utf-8 -*-
"""SAM module models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select import LookupChannel
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    Named,
    TimeTrackable,
    WithConcurrentGetOrCreate,
)
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from ralph_assets.models_assets import AssetManufacturer, AssetType

class LicenceType(Named):
    """The type of a licence"""


class SoftwareCategory(Named):
    """The category of the licensed software"""
    asset_type = models.PositiveSmallIntegerField(
        choices=AssetType()
    )

    @property
    def licences(self):
        """Iterate over licences."""
        for licence in self.licence_set.all():
            yield licence


class Licence(MPTTModel, TimeTrackable, WithConcurrentGetOrCreate):
    """A set of licences for a single software with a single expiration date"""
    manufacturer = models.ForeignKey(
        AssetManufacturer,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    licence_type = models.ForeignKey(
        LicenceType,
        on_delete=models.PROTECT,
    )
    software_category = models.ForeignKey(
        SoftwareCategory,
        on_delete=models.PROTECT,
    )
    number_bought = models.IntegerField()
    sn = models.CharField(
        verbose_name=_('SN / Key'),
        max_length=200,
        null=True,
        blank=True,
        unique=True,
    )
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
    )
    niw = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    bought_date = models.DateField()
    valid_thru = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank if this licence is perpetual",
    )
    order_no = models.CharField(max_length=50, null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    accounting_id = models.CharField(
        max_length=200,
        null=True,
    )
    asset_type = models.PositiveSmallIntegerField(
        choices=AssetType()
    )
    used = models.IntegerField()

    def __str__(self):
        return "{} x {} - {}".format(
            self.number_bought,
            self.software_category.name,
            self.bought_date,
        )

    @property
    def url(self):
        return reverse('edit_licence', kwargs={
            'licence_id': self.id,
            'mode': {
                AssetType.data_center: 'dc',
                AssetType.back_office: 'back_office',
            }[self.asset_type],
        })

class SoftwareCategoryLookup(LookupChannel):
    model = SoftwareCategory

    def get_query(self, q, request):
        return SoftwareCategory.objects.filter(
            name__icontains=q
        ).order_by('name')[:10]

    def get_result(self, obj):
        return obj.name

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return escape(obj.name)
