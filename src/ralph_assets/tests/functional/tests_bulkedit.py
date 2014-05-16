# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph_assets import models_assets
from ralph_assets.models_assets import AssetStatus
from ralph_assets.tests import util as utils
from ralph_assets.tests.util import (
    create_asset,
    create_model,
    create_category,
    get_bulk_edit_post_data,
)
from ralph.ui.tests.global_utils import login_as_su
import unittest


class TestBulkEdit(TestCase):
    """Test bulkedit for generic actions

    Scenario:
    1. Add two assets
    2. Check if data was saved
    """

    def setUp(self):
        self.client = login_as_su()
        self.category = create_category()
        self.asset = create_asset(
            sn='1111-1111-1111-1111',
        )
        self.asset1 = create_asset(
            sn='2222-2222-2222-2222',
        )
        self.user = utils.create_user()
        self.owner = self.user
        self.model = create_model(category=self.category)  # u'Model1'
        self.model1 = create_model(name='Model2', category=self.category)
        self.warehouse = utils.create_warehouse()
        self.assetOwner = utils.create_asset_owner()
        self.asset_service = utils.create_service()

    def test_edit_via_bulkedit_form(self):
        url = '/assets/dc/bulkedit/?select=%s&select=%s' % (
            self.asset.id, self.asset1.id)
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        post_data = get_bulk_edit_post_data(
            {
                'model': self.model.id,
                'invoice_no': 'Invoice No1',
                'order_no': 'Order No1',
                'invoice_date': '2012-02-02',
                'status': AssetStatus.in_progress.id,
                'sn': '3333-3333-3333-3333',
                'barcode': 'bc-3333-3333-3333-3333',
            },
            {
                'model': self.model1.id,
                'invoice_no': 'Invoice No2',
                'order_no': 'Order No2',
                'invoice_date': '2011-02-03',
                'status': AssetStatus.waiting_for_release.id,
                'sn': '4444-4444-4444-4444',
                'barcode': 'bc-4444-4444-4444-4444',
            },
        )

        response = self.client.post(url, post_data, follow=True)

        # Find success message
        self.assertTrue('Changes saved.' in response.content)

        # if everything is ok, server return response code = 302, and
        # redirect us to /assets/dc/search given response code 200
        self.assertRedirects(
            response,
            url,
            status_code=302,
            target_status_code=200,
        )

        # Simulate reopening bulkedit form to check if data were written
        new_view = self.client.get(url)
        fields = new_view.context['formset'].queryset

        correct_data = [
            dict(
                model=unicode(self.model),
                invoice_no='Invoice No1',
                order_no='Order No1',
                invoice_date='2012-02-02',
                status=AssetStatus.in_progress.id,
                sn='3333-3333-3333-3333',
                barcode='bc-3333-3333-3333-3333',
            ),
            dict(
                model=unicode(self.model1),
                invoice_no='Invoice No2',
                order_no='Order No2',
                invoice_date='2011-02-03',
                status=AssetStatus.waiting_for_release.id,
                sn='4444-4444-4444-4444',
                barcode='bc-4444-4444-4444-4444',
            )
        ]
        counter = 0
        for data in correct_data:
            for key in data.keys():
                self.assertEqual(
                    unicode(getattr(fields[counter], key)), unicode(data[key])
                )
            counter += 1

    def test_showing_dc_form_data(self):
        """
        1. add DC asset,
        2. open asset in bulk mode,
        3. check if all fields are set like the added asset.
        """
        asset_data = {
            'type': models_assets.AssetType.data_center,
            'status': models_assets.AssetStatus.in_progress,
            'barcode': 'barcode',
            'model': self.model,
            'user': self.user,
            'owner': self.user,
            'warehouse': self.warehouse,
            'sn': 'sn',
            'property_of': self.assetOwner,
            'service_name': self.asset_service,
            'invoice_no': 'invoice_no',
            'invoice_date': '2011-11-14',
            'price': '100',
            'task_url': 'www.test.com',
            'deprecation_rate': '25',
            'order_no': 'order_no',
            'source': models_assets.AssetSource.shipment,
        }
        asset = create_asset(**asset_data)

        url = '/assets/dc/bulkedit/?select={}'.format(asset.id)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        form_excluded_fields = ['type']
        for field_name, value in asset_data.items():
            if field_name in form_excluded_fields:
                continue
            form_val = unicode(
                resp.context['formset'].forms[0][field_name].value()
            )
            if isinstance(value, basestring):
                expected = asset_data[field_name]
            else:
                expected = asset_data[field_name].id
            msg = 'Bulkedit field "{}" got "{}" instead of "{}"'.format(
                field_name, form_val, expected
            )
            self.assertEqual(form_val, unicode(expected), msg)

    @unittest.skip("to be implement")
    def test_showing_bo_form_data(self):
        pass
