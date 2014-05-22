# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import uuid

from django.test import TestCase
from django.core.urlresolvers import reverse

from ralph_assets.models_assets import (AssetStatus, AssetType)
from ralph_assets.tests.util import (
    create_asset,
    create_model,
    create_warehouse,
)
from ralph.ui.tests.global_utils import login_as_su


class TestDataDisplay(TestCase):
    """Test check if data from database are displayed on screen"""

    def setUp(self):
        self.client = login_as_su()
        asset_fields = dict(
            barcode='123456789',
            invoice_no='Invoice #1',
            order_no='Order #1',
            invoice_date=datetime.date(2001, 1, 1),
            sn='0000-0000-0000-0000',
        )
        self.asset = create_asset(**asset_fields)

    def test_display_data_in_table(self):
        get_search_page = self.client.get('/assets/dc/search')
        self.assertEqual(get_search_page.status_code, 200)

        # Test if data from database are displayed in correct row.
        first_table_row = get_search_page.context_data['bob_page'][0]
        self.assertEqual(self.asset, first_table_row)
        self.assertItemsEqual(
            [
                first_table_row.barcode,
                first_table_row.invoice_no,
                first_table_row.order_no,
                unicode(first_table_row.invoice_date),
                first_table_row.sn,
                AssetType.name_from_id(first_table_row.type),
                AssetStatus.name_from_id(first_table_row.status),
                first_table_row.model.name,
                first_table_row.warehouse.name,
            ],
            [
                u'123456789',
                u'Invoice #1',
                u'Order #1',
                u'2001-01-01',
                u'0000-0000-0000-0000',
                u'Model1',
                'data_center',
                'new',
                'Warehouse',
            ]
        )


class DeviceEditViewTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.asset_src = create_asset('123-456-789')
        self.asset_dest = create_asset('987-832-668')

        self.model = create_model()
        self.warehouse = create_warehouse()

    def _create_part(self, asset, model, warehouse):
        url_kwargs = {'mode': 'dc'}
        url = reverse('add_part', kwargs=url_kwargs)
        url += '?device={}'.format(asset.id)

        post_data = {
            'asset': '1',  # submit button
            'model': model.id,
            'warehouse': warehouse.id,
            'device': asset.id,
            'type': '1',
            'sn': str(uuid.uuid1()),
            'deprecation_rate': '25',
        }
        return self.client.post(url, post_data, follow=True)

    def _move_part(self, asset_src, post_data):
        url_kwargs = {'mode': 'back_office', 'asset_id': asset_src.id}
        url = reverse('device_edit', kwargs=url_kwargs)
        return self.client.post(url, post_data, follow=True)

    def test_create_part(self):
        """Create part in add part view."""
        response = self._create_part(
            self.asset_src, self.model, self.warehouse,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['asset'].pk)

    def test_move_part(self):
        """Move part in edit device view.
        Scenario:
         - add part to specified device,
         - go to edit device view,
         - move part from actual device to another device.
        """
        part = self._create_part(
            self.asset_src, self.model, self.warehouse,
        ).context['asset']

        url_kwargs = {'mode': 'back_office', 'asset_id': self.asset_src.id}
        url = reverse('device_edit', kwargs=url_kwargs)
        response = self.client.get(url)
        self.assertContains(response, part)

        post_data = {
            'move_parts': '1',  # submit form
            'new_asset': self.asset_dest.id,
            'part_ids': [part.id],
        }
        response = self._move_part(self.asset_src, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, part)

        url_kwargs = {'mode': 'back_office', 'asset_id': self.asset_dest.id}
        url = reverse('device_edit', kwargs=url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, part)

    def test_move_few_part(self):
        """Move part in edit device view.
        Scenario:
         - add part to specified device,
         - go to edit device view,
         - move few parts from actual device to another.
        """
        parts = []
        for i in range(5):
            part = self._create_part(
                self.asset_src, self.model, self.warehouse,
            ).context['asset']
            parts.append(part)

        url_kwargs = {'mode': 'back_office', 'asset_id': self.asset_src.id}
        url = reverse('device_edit', kwargs=url_kwargs)
        response = self.client.get(url)
        for part in parts:
            self.assertContains(response, part)

        post_data = {
            'move_parts': '1',  # submit form
            'new_asset': self.asset_dest.id,
            'part_ids': [part.id for part in parts],
        }
        response = self._move_part(self.asset_src, post_data)
        self.assertEqual(response.status_code, 200)
        for part in parts:
            self.assertNotContains(response, part)

        url_kwargs = {'mode': 'back_office', 'asset_id': self.asset_dest.id}
        url = reverse('device_edit', kwargs=url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, part)

    def test_move_part_error_new_asset(self):
        """Move part in edit device view.
        Scenario:
         - add part to specified device,
         - go to edit device view,
         - user fill all required field except new_asset,
         - user see a message: 'Source device asset does not exist'
        """
        msg_error = 'Source device asset does not exist'
        part = self._create_part(
            self.asset_src, self.model, self.warehouse,
        ).context['asset']

        post_data = {
            'move_parts': '1',
            'part_ids': [part.id],
        }
        response = self._move_part(self.asset_src, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, msg_error)
        self.assertContains(response, part)

    def test_move_part_error_part_ids(self):
        """Move part in edit device view.
        Scenario:
         - add part to specified device,
         - go to edit device view,
         - user fill all required field but doesn't select any part,
         - user see a message: 'Please select one or more parts'
        """
        msg_error = 'Please select one or more parts'
        part = self._create_part(
            self.asset_src, self.model, self.warehouse,
        ).context['asset']

        post_data = {
            'move_parts': '1',
            'new_asset': self.asset_dest.id,
        }
        response = self._move_part(self.asset_src, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, msg_error)
        self.assertContains(response, part)
