# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph_assets.models_assets import Asset

def get_assets():
    """Yields dicts describing all assets"""
    for asset in Asset.objects_dc.all():
        yield {
            'asset_id': asset.id,
            'ralph_id': asset.device_info.ralph_device_id,
            'slots': asset.slots,
            'price': asset.price,
            'is_deprecated': asset.is_deprecated()
        }
