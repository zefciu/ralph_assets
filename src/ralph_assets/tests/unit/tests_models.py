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
from ralph_assets.models_assets import Asset, DeviceInfo
from ralph_assets.tests.util import create_asset
from ralph_assets.api_pricing import get_assets


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
			},
		)
		self.device_info = DeviceInfo(
			ralph_device=self.device,
			size=6,
		)
		self.device_info.save()
		self.asset = create_asset(
            sn='1111-1111-1111-1111',
            invoice_date='2012-11-28',
            support_period=1,
            slots='12.0',
            price=100,
            device_info=self.device_info,
        )

	def tests_api(self):
		for item in get_assets():
			self.assertEqual(item['name'], self.asset.sn)
			self.assertEqual(item['asset_id'], self.asset.id)
			self.assertEqual(item['ralph_id'], self.device_info.ralph_device.id)
			self.assertEqual(item['slots'], self.asset.slots)
			self.assertEqual(item['price'], self.asset.price)
			self.assertEqual(item['is_deprecated'], self.asset.is_deprecated())
