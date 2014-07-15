# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.ui.tests.global_utils import login_as_su
from ralph_assets.models_assets import AssetCategory
from ralph_assets.tests.utils.assets import BOAssetFactory
from ralph_assets.tests.utils.assets import (
    AssetModelFactory,
)


class TestReportCategoryTreeView(TestCase):
    """
    sdas"""
    def setUp(self):
        self.client = login_as_su()
        self._create_models()

    def _create_models(self):
        self.keyboard_model = AssetModelFactory(
            category=AssetCategory.objects.get(name="Keyboard")
        )
        self.mouse_model = AssetModelFactory(
            category=AssetCategory.objects.get(name="Mouse")
        )
        self.pendrive_model = AssetModelFactory(
            category=AssetCategory.objects.get(name="Pendrive")
        )

        self.model_monitor = AssetModelFactory(
            category=AssetCategory.objects.get(name="Monitor")
        )
        self.navigation_model = AssetModelFactory(
            category=AssetCategory.objects.get(name="Navigation")
        )
        self.scanner_model = AssetModelFactory(
            category=AssetCategory.objects.get(name="Scanner")
        )
        self.shredder_model = AssetModelFactory(
            category=AssetCategory.objects.get(name="Shredder")
        )

    def _create_assets(self):
        [BOAssetFactory(**{'model': self.keyboard_model}) for _ in xrange(6)]
        [BOAssetFactory(**{'model': self.mouse_model}) for _ in xrange(2)]
        [BOAssetFactory(**{'model': self.pendrive_model}) for _ in xrange(2)]

        [BOAssetFactory(**{'model': self.model_monitor}) for _ in xrange(2)]
        [BOAssetFactory(**{'model': self.navigation_model}) for _ in xrange(2)]
        [BOAssetFactory(**{'model': self.scanner_model}) for _ in xrange(3)]
        [BOAssetFactory(**{'model': self.shredder_model}) for _ in xrange(3)]

    def test_category_model_tree(self):
        url = reverse(
            'report', kwargs={'mode': 'back_office', 'slug': 'category-model'},
        )
        response = self.client.get(url, follow=True)
        report_dict = response.context_data.get('report_dict')
        back_office_dict = report_dict['BACK OFFICE']
        equipment_dict = back_office_dict['children']['EQUIPMENT']
        accesories_dict = back_office_dict['children']['ACCESSORIES']

        self.assertEqual(back_office_dict['count'], 20)
        self.assertEqual(equipment_dict['count'], 10)
        self.assertEqual(accesories_dict['count'], 10)

        accesories_children = accesories_dict['children']
        self.assertEqual(accesories_children['Keyboard']['count'], 6)
        self.assertEqual(accesories_children['Mouse']['count'], 2)
        self.assertEqual(accesories_children['Pendrive']['count'], 2)

        equipment_children = equipment_dict['children']
        self.assertEqual(equipment_children['Monitor']['count'], 2)
        self.assertEqual(equipment_children['Navigation']['count'], 2)
        self.assertEqual(equipment_children['Scanner']['count'], 3)
        self.assertEqual(equipment_children['Shredder']['count'], 3)
