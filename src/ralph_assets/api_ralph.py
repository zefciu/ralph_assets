# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph_assets.models_assets import Asset, AssetSource, AssetStatus


def get_asset(device_id):
    try:
        asset = Asset.objects.get(device_info__ralph_device_id=device_id)
    except Asset.DoesNotExist:
        return
    return {
        'asset_id': asset.id,
        'model': asset.model.name,
        'manufacturer': asset.model.manufacturer.name,
        'source': str(AssetSource.from_id(asset.source)),
        'invoice_no': asset.invoice_no,
        'order_no': asset.order_no,
        'invoice_date': asset.invoice_date,
        'sn': asset.sn,
        'barcode': asset.barcode,
        'price': asset.price,
        'support_price': asset.support_price,
        'support_period': asset.support_period,
        'support_type': asset.support_type,
        'support_void_reporting': asset.support_void_reporting,
        'provider': asset.provider,
        'status': str(AssetStatus.from_id(asset.status)),
        'remarks': asset.remarks,
        'niw': asset.niw,
        'warehouse': asset.warehouse.name,
        'request_date': asset.request_date,
        'delivery_date': asset.delivery_date,
        'production_use_date': asset.production_use_date,
        'provider_order_date': asset.provider_order_date,
        'category': asset.category.name,
        'slots': asset.slots,
        'price': asset.price,
        'deprecation_rate': asset.deprecation_rate,
        'is_deprecated': asset.is_deprecated(),
        'size': asset.device_info.size,
        'u_level': asset.device_info.u_level,
        'u_height': asset.device_info.u_height,
        'rack': asset.device_info.rack,
    }

