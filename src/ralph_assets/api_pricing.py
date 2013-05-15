# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph_assets.models_assets import Asset

def get_assets():
    """Yields dicts describing all assets"""
    for asset in Asset.admin_objects_dc.all():
    	ralph_device = asset.device_info.ralph_device
        yield {
            'asset_id': asset.id,
            'ralph_id': ralph_device.id if ralph_device else None,
            'slots': asset.slots,
            'price': asset.price,
            'is_deprecated': asset.is_deprecated()
        }
