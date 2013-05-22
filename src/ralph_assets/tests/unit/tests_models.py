# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase

from ralph.business.models import Venture
from ralph.discovery.models import Device, DeviceType
from ralph.ui.tests.util import create_device
from ralph_assets.models_assets import Asset, DeviceInfo, PartInfo, AssetModel
from ralph_assets.tests.util import create_asset
from ralph_assets.api_pricing import get_assets, get_asset_parts


class TestModelAsset(TestCase):
    def setUp(self):
        self.asset = create_asset(
            sn='1111-1111-1111-1111',
            invoice_date='2012-11-28',
            support_period=1,
        )
        self.asset2 = create_asset(
            sn='1111-1111-1111-1112',
            invoice_date='2012-11-28',
            support_period=120,
        )

    def test_is_deperecation(self):
        self.assertEqual(self.asset.is_deprecated(), True)
        self.assertEqual(self.asset2.is_deprecated(), False)


class TestApiAssets(TestCase):
    def setUp(self):
        venture = Venture(name='Infra').save()
        self.device = create_device(
            device={
                'sn': 'srv-1',
                'model_name': 'server',
                'model_type': DeviceType.virtual_server,
                'venture': venture,
                'name': 'Srv 1',
                'purchase_date': '2012-11-28',
                'sn': 'aaaa-aaaa-aaaa-aaaa',
                'barcode': 'bbbb-bbbb-bbbb-bbbb',
            },
        )
        self.device_info = DeviceInfo(
            ralph_device_id=self.device.id,
            size=6,
        )
        self.device_info.save()

        self.asset = create_asset(
            sn='1111-1111-1111-1111',
            invoice_date='2012-11-28',
            support_period=1,
            slots=12.0,
            price=100,
            device_info=self.device_info,
        )
        self.device2 = create_device(
            device={
                'sn': 'srv-2',
                'model_name': 'server',
                'model_type': DeviceType.virtual_server,
                'venture': venture,
                'name': 'Srv 2',
                'purchase_date': '2012-11-28',
                'sn': 'cccc-cccc-cccc-cccc',
                'barcode': 'dddd-dddd-dddd-dddd',
            },
        )
        self.device_info2 = DeviceInfo(
            ralph_device_id=self.device2.id,
            size=6,
        )
        self.device_info.save()
        self.part_info = PartInfo(device=self.asset)
        self.part_info.save()
        self.asset2 = create_asset(
            sn='1111-1111-1111-11132',
            invoice_date='2012-11-28',
            support_period=1,
            slots=12.0,
            price=100,
            device_info=self.device_info2,
            part_info=self.part_info,
        )

    def tests_api_asset(self):
        for item in get_assets():
            self.assertEqual(item['asset_id'], self.asset.id)
            self.assertEqual(item['ralph_id'], self.device_info.ralph_device_id)
            self.assertEqual(item['slots'], self.asset.slots)
            self.assertEqual(item['price'], self.asset.price)
            self.assertEqual(item['is_deprecated'], self.asset.is_deprecated())
            self.assertEqual(item['sn'], self.asset.sn)
            self.assertEqual(item['barcode'], self.asset.barcode)

    def tests_api_asset_part(self):
        for item in get_asset_parts():
            self.assertEqual(item['price'], 100)
            self.assertEqual(item['is_deprecated'], True)
            model = AssetModel.objects.get(name="Model1")
            self.assertEqual(item['model'], model.name)
            self.assertEqual(item['asset_id'], self.asset2.id)
            self.assertEqual(item['asset_parent_id'], self.asset.id)
            self.assertEqual(item['sn'], self.asset.sn)
            self.assertEqual(item['barcode'], self.asset.barcode)
