# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph_assets.models_assets import Asset
from ralph_assets.tests.util import (
    create_asset,
    create_category,
    create_model,
    create_warehouse,
    create_manufacturer,
)


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


