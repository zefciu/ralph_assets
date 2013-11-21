# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph_assets.models_assets import Asset


def get_assets(date):
    """Yields dicts describing all assets"""
    for asset in Asset.objects_dc.filter(
        part_info_id=None,
        invoice_date__lte=date,
    ):
        device_info = asset.device_info
        yield {
            'asset_id': asset.id,
            'barcode': asset.barcode,
            'is_deprecated': asset.is_deprecated(date=date),
            'price': asset.price,
            'ralph_id': device_info.ralph_device_id if device_info else None,
            'slots': asset.slots,
            'sn': asset.sn,
            'price': asset.price,
            'deprecation_rate': asset.deprecation_rate,
        }


def get_asset_parts():
    for asset in Asset.objects_dc.all():
        for part in asset.get_parts():
            device_info = asset.device_info
            yield {
                'asset_id': part.id,
                'barcode': asset.barcode,
                'is_deprecated': part.is_deprecated(),
                'model': part.model.name if part.model else None,
                'price': part.price,
                'ralph_id': device_info.ralph_device_id if device_info else None,  # noqa
                'sn': asset.sn,
                'deprecation_rate': asset.deprecation_rate,
                'is_deprecated': part.is_deprecated(),
            }
