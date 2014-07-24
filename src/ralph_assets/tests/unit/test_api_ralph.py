# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph_assets.api_ralph import get_asset
from ralph_assets.tests.utils.assets import (
    DCAssetFactory,
    AssetCategoryFactory,
    AssetModelFactory,
)
from ralph_assets.tests.utils.supports import DCSupportFactory


class TestApiRalph(TestCase):
    """Test internal API for Ralph"""

    def test_get_asset(self):
        """Test get asset information by ralph_device_id."""
        self.support1 = DCSupportFactory()
        self.support2 = DCSupportFactory()
        self.category = AssetCategoryFactory()
        self.model = AssetModelFactory(category=self.category)
        self.asset = DCAssetFactory(
            model=self.model,
            supports=[self.support1, self.support2],
        )
        asset_data = get_asset(self.asset.device_info.ralph_device_id)
        self.assertEqual(asset_data['sn'], self.asset.sn)
        self.assertEqual(asset_data['barcode'], self.asset.barcode)
        self.assertEqual(asset_data['supports'][0]['name'], self.support1.name)
        self.assertEqual(asset_data['supports'][0]['url'], self.support1.url)
        self.assertEqual(asset_data['supports'][1]['name'], self.support2.name)
        self.assertEqual(asset_data['supports'][1]['url'], self.support2.url)
        self.assertEqual(
            asset_data['required_support'], self.asset.required_support,
        )

    def test_get_asset_without_asset(self):
        self.assertEqual(get_asset(666), None)

    def test_get_asset_with_empty_asset_source(self):
        """Getting an asset with empty 'source' field should also succeed."""
        self.category = AssetCategoryFactory()
        self.model = AssetModelFactory(category=self.category)
        self.asset = DCAssetFactory(model=self.model, source=None)
        self.asset_data = get_asset(self.asset.device_info.ralph_device_id)
        self.assertEqual(self.asset_data['source'], None)
