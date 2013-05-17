# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph_assets.models_assets import Asset

def get_assets():
    """Yields dicts describing all assets"""
    for asset in Asset.objects_dc.filter(part_info_id=None):
        device_info = asset.device_info
        yield {
            'asset_id': asset.id,
            'ralph_id': device_info.ralph_device_id if device_info else None,
            'slots': asset.slots,
            'price': asset.price,
            'is_deprecated': asset.is_deprecated()
        }

def get_asset_parts():
    for asset in Asset.objects_dc.all():
        for part in asset.get_parts():
            device_info = asset.device_info
            yield {
                'asset_id': asset.id,
                'ralph_id': device_info.ralph_device_id if device_info else None,
                'model': part.model.name,
                'price': part.price,
                'is_deprecated': part.is_deprecated(),
            }
