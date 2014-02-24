"""SAM module models."""

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    Named,
    TimeTrackable,
    WithConcurrentGetOrCreate,
)
from ralph_assets.models_assets import AssetManufacturer, AssetType
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

class LicenceType(Named):
    """The type of a licence"""


class SoftwareCategory(Named):
    """The category of the licensed software"""


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

    @property
    def url(self):
        return reverse('edit_licence', kwargs={
            'licence_id': self.id,
            'mode': {
                AssetType.data_center: 'dc',
                AssetType.back_office: 'back_office',
            }[self.asset_type],
        })
