# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import uuid
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from ralph_assets import models_assets
from ralph_assets import models_support
from ralph_assets import models_sam
from ralph_assets.tests.utils import assets as assets_utils
from ralph_assets.tests.utils import sam as sam_utils
from ralph_assets.tests.utils import supports as support_utils
from ralph_assets.tests.utils.assets import (
    BOAssetFactory,
    AssetFactory,
    AssetModelFactory,
    DCAssetFactory,
    WarehouseFactory,
)
from ralph_assets.tests.utils.sam import LicenceFactory
from ralph.ui.tests.global_utils import login_as_su


def update(_dict, obj, keys):
    """
    Update *_dict* with *obj*'s values from keys.
    """
    for field_name in keys:
        _dict['hostname'] = getattr(obj, field_name)
    return _dict


def get_asset_data():
    """
    Common asset data for DC & BO.

    This can't be a just module dict, becasue these data include factories
    which are not accessible during module import causing error.
    """
    return {
        'asset': '',  # required if asset (instead of *part*) is edited
        'barcode': 'barcode1',
        'budget_info': assets_utils.BudgetInfoFactory().id,
        'delivery_date': datetime.date(2013, 1, 7),
        'deprecation_end_date': datetime.date(2013, 7, 25),
        'deprecation_rate': 77,
        'hostname': 'POLPC12345',
        'invoice_date': datetime.date(2009, 2, 23),
        'invoice_no': 'Invoice no #3',
        'loan_end_date': datetime.date(2013, 12, 29),
        'location': 'location #3',
        'model': assets_utils.AssetModelFactory().id,
        'niw': 'Inventory number #3',
        'order_no': 'Order no #3',
        'owner': assets_utils.UserFactory().id,
        'price': Decimal('43.45'),
        'property_of': assets_utils.AssetOwnerFactory().id,
        'provider': 'Provider #3',
        'provider_order_date': datetime.date(2014, 3, 17),
        'remarks': 'Remarks #3',
        'request_date': datetime.date(2014, 6, 9),
        'service_name': assets_utils.ServiceFactory().id,
        'source': models_assets.AssetSource.shipment.id,
        'status': models_assets.AssetStatus.new.id,
        'task_url': 'http://www.url-3.com/',
        'user': assets_utils.UserFactory().id,
        'warehouse': assets_utils.WarehouseFactory().id,
    }


def check_fields(testcase, correct_data, object_to_check):
    """
    Checks if *object_to_check* has the same data as *correct_data*

    :param tc: testcase object
    :param correct_data: list with of tuples: (property_name, expected_value)
    :param object_to_check: dict with requried data
    """
    for prop_name, expected in correct_data:
        object_value = getattr(object_to_check, prop_name)
        try:
            object_value = object_value.id
        except AttributeError:
            pass
        object_value, expected = (
            unicode(object_value), unicode(expected)
        )
        msg = 'Object prop. "{}" is "{}" instead of "{}"'.format(
            prop_name, repr(object_value), repr(expected)
        )
        testcase.assertEqual(object_value, expected, msg)


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
        self.asset = AssetFactory(**asset_fields)

    def test_display_data_in_table(self):
        get_search_page = self.client.get('/assets/dc/search')
        self.assertEqual(get_search_page.status_code, 200)

        # Test if data from database are displayed in correct row.
        first_table_row = get_search_page.context_data['bob_page'][0]
        self.assertEqual(self.asset, first_table_row)


class TestDevicesView(TestCase):
    """
    Parent class for common stuff for Test(DataCenter|BackOffice)DeviceView.
    """

    def prepare_readonly_fields(self, new_asset_data, asset, readonly_fields):
        update(new_asset_data, asset, readonly_fields)

    def _update_with_supports(self, _dict):
        supports = [
            support_utils.DCSupportFactory().id,
            support_utils.BOSupportFactory().id,
        ]
        supports_value = '|{}|'.format('|'.join(map(str, supports)))
        _dict.update(dict(supports=supports_value))
        return supports

    def _check_asset_supports(self, asset, expected_supports):
        self.assertEqual(
            len(asset.support_set.all()), len(expected_supports),
        )
        del self.new_asset_data['supports']


class TestDataCenterDevicesView(TestDevicesView, TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.mode = 'dc'
        self.asset_data = get_asset_data()
        self.asset_data.update({
            'type': models_assets.AssetType.data_center.id,
        })
        self.device_data = {
            'ralph_device_id': '',
            'u_height': 14,
            'u_level': 21,
        }

    def test_add_device(self):
        """
        Add device with all fields filled.

        - send the full asset's data with post request
        - get saved asset from db
        - asserts all db asset's fields with request's data
        """
        asset_data = self.asset_data.copy()
        asset_data.update({
            'sn': str(uuid.uuid1()),
        })
        device_data = self.device_data.copy()
        request_data = {}
        request_data.update(asset_data)
        request_data.update(device_data)
        url = reverse('add_device', kwargs={'mode': self.mode})
        existing_assets = models_assets.Asset.objects.reverse()
        asset_id = existing_assets[0].id + 1 if existing_assets else 1
        response = self.client.post(url, request_data)
        self.assertRedirects(
            response,
            reverse('device_edit', kwargs={
                'mode': self.mode, 'asset_id': asset_id
            }),
            status_code=302,
            target_status_code=200,
        )
        asset = models_assets.Asset.objects.filter(pk=asset_id).get()
        del asset_data['asset']
        check_fields(self, asset_data.items(), asset)
        device_data['ralph_device_id'] = asset_id
        check_fields(self, device_data.items(), asset.device_info)

    def test_edit_device(self):
        """
        Add device with all fields filled.

        - generate asset data d1
        - create asset a1
        - send data d1 via edit request to a1
        - get a1 from db
        - assert a1's data is the same as d1 data
        """
        self.new_asset_data = self.asset_data.copy()
        supports = self._update_with_supports(self.new_asset_data)
        new_device_data = self.device_data.copy()
        asset = DCAssetFactory()
        edited_data = {}
        edited_data.update(self.new_asset_data)
        edited_data.update(new_device_data)
        url = reverse('device_edit', kwargs={
            'mode': self.mode,
            'asset_id': asset.id,
        })
        response = self.client.post(url, edited_data)
        self.assertRedirects(
            response, url, status_code=302, target_status_code=200,
        )
        asset = models_assets.Asset.objects.get(pk=asset.id)
        del self.new_asset_data['asset']
        self._check_asset_supports(asset, supports)
        self.prepare_readonly_fields(self.new_asset_data, asset, ['hostname'])
        check_fields(self, self.new_asset_data.items(), asset)
        new_device_data['ralph_device_id'] = None
        check_fields(self, new_device_data.items(), asset.device_info)


class TestBackOfficeDevicesView(TestDevicesView, TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.mode = 'back_office'
        self.asset_data = get_asset_data()
        self.asset_data.update({
            'type': models_assets.AssetType.back_office.id,
        })
        self.office_data = {
            'coa_oem_os': assets_utils.CoaOemOsFactory().id,
            'purpose': models_assets.AssetPurpose.others.id,
            'license_key': str(uuid.uuid1()),
            'imei': assets_utils.generate_imei(15),
            'coa_number': str(uuid.uuid1()),
        }

    def test_add_device(self):
        """
        Add device with all fields filled.

        - send the full asset's data with post request
        - get saved asset from db
        - asserts all db asset's fields with request's data
        """
        asset_data = self.asset_data.copy()
        asset_data.update({
            'sn': str(uuid.uuid1()),
        })
        office_data = self.office_data.copy()
        request_data = {}
        request_data.update(asset_data)
        request_data.update(office_data)
        url = reverse('add_device', kwargs={'mode': self.mode})
        existing_assets = models_assets.Asset.objects.reverse()
        asset_id = existing_assets[0].id + 1 if existing_assets else 1
        response = self.client.post(url, request_data)
        self.assertRedirects(
            response,
            reverse('device_edit', kwargs={
                'mode': self.mode, 'asset_id': asset_id
            }),
            status_code=302,
            target_status_code=200,
        )
        asset = models_assets.Asset.objects.filter(pk=asset_id).get()
        del asset_data['asset']
        check_fields(self, asset_data.items(), asset)
        check_fields(self, office_data.items(), asset.office_info)

    def test_edit_device(self):
        """
        Add device with all fields filled.

        - generate asset data d1
        - create asset a1
        - send data d1 via edit request to a1
        - get a1 from db
        - assert a1's data is the same as d1 data
        """
        self.new_asset_data = self.asset_data.copy()
        supports = self._update_with_supports(self.new_asset_data)
        new_office_data = self.office_data.copy()
        asset = BOAssetFactory()
        edited_data = {}
        edited_data.update(self.new_asset_data)
        edited_data.update(new_office_data)
        url = reverse('device_edit', kwargs={
            'mode': self.mode,
            'asset_id': asset.id,
        })
        response = self.client.post(url, edited_data)
        self.assertRedirects(
            response, url, status_code=302, target_status_code=200,
        )
        asset = models_assets.Asset.objects.get(pk=asset.id)
        self.prepare_readonly_fields(self.new_asset_data, asset, ['hostname'])
        del self.new_asset_data['asset']
        self._check_asset_supports(asset, supports)
        check_fields(self, self.new_asset_data.items(), asset)
        check_fields(self, new_office_data.items(), asset.office_info)


class TestLicencesView(TestCase):
    """This test case concern all licences views."""
    def setUp(self):
        self.client = login_as_su()
        self.license_data = {
            'accounting_id': '1',
            'asset_type': models_assets.AssetType.back_office.id,
            # TODO: this field is not saving 'assets':'|{}|'.format(asset.id),
            'budget_info': assets_utils.BudgetInfoFactory().id,
            'invoice_date': datetime.date(2014, 06, 11),
            'invoice_no': 'Invoice no',
            'licence_type': sam_utils.LicenceTypeFactory().id,
            'license_details': 'licence_details',
            'manufacturer': assets_utils.AssetManufacturerFactory().id,
            'niw': 'Inventory number',
            'number_bought': '99',
            'order_no': 'Order no',
            'price': Decimal('100.99'),
            'property_of': assets_utils.AssetOwnerFactory().id,
            'provider': 'Provider',
            'remarks': 'Additional remarks',
            'service_name': assets_utils.ServiceFactory().id,
            'sn': 'Licence key',
            'software_category': sam_utils.SoftwareCategoryFactory().id,
            'valid_thru': datetime.date(2014, 06, 10),
        }

        self.licence = LicenceFactory()

    def _field_in_edit_form(self, field, modes=None):
        url = reverse('edit_licence', args=(self.licence.pk,))
        response = self.client.get(url)
        self.assertContains(response, 'id_{}'.format(field))

    def test_add_license(self):
        """
        Add license with all fields filled.

        - send the full license's data with post request
        - get saved license from db
        - asserts all db license's fields with request's data
        """
        request_data = self.license_data.copy()
        response = self.client.post(reverse('add_licence'), request_data)
        self.assertRedirects(
            response, reverse('licence_list'), status_code=302,
            target_status_code=200,
        )
        license = models_sam.Licence.objects.reverse()[0]
        check_fields(self, request_data.items(), license)

    def test_edit_license(self):
        """
        Edit license with all fields filled.
        - generate license data d1
        - create license l1
        - send data d1 via edit request to l1
        - get l1 from db
        - assert l1's data is the same as d1 data
        """
        new_license_data = self.license_data.copy()
        license = LicenceFactory()
        url = reverse('edit_licence', kwargs={
            'licence_id': license.id,
        })
        response = self.client.post(url, new_license_data)
        self.assertRedirects(
            response, url, status_code=302, target_status_code=200,
        )
        license = models_sam.Licence.objects.get(pk=license.id)
        check_fields(self, new_license_data.items(), license)

    def test_edit_form_contains_remarks_field(self):
        self._field_in_edit_form('remarks')

    def test_edit_form_contains_service_name_field(self):
        self._field_in_edit_form('service_name')

    def test_bulk_edit(self):
        num_of_licences = 10
        fields = [
            'accounting_id',
            'asset_type',
            'assets',
            'invoice_date',
            'invoice_no',
            'licence_type',
            'niw',
            'number_bought',
            'order_no',
            'parent',
            'price',
            'property_of',
            'provider',
            'remarks',
            'service_name',
            'sn',
            'software_category',
            'valid_thru',
        ]
        licences = [LicenceFactory() for _ in range(num_of_licences)]
        url = reverse('licence_bulkedit')
        url += '?' + '&'.join(['select={}'.format(obj.pk) for obj in licences])
        response = self.client.get(url, follow=True)

        for key in fields:
            self.assertIn(
                key, response.context['formset'][0].fields.keys()
            )


class TestSupportsView(TestCase):
    """This test case concern all supports views."""

    def setUp(self):
        self.client = login_as_su()
        support_utils.SupportTypeFactory().id
        self.support_data = dict(
            additional_notes="Additional notes",
            # asset='',  # button, skip it
            asset_type=101,
            contract_id='1',
            contract_terms='Contract terms',
            date_from=datetime.date(2014, 06, 17),
            date_to=datetime.date(2014, 06, 18),
            description='Description',
            escalation_path='Escalation path',
            invoice_date=datetime.date(2014, 06, 19),
            invoice_no='Invoice no',
            name='name',
            period_in_months='12',
            price=Decimal('99.99'),
            producer='Producer',
            property_of=assets_utils.AssetOwnerFactory().id,
            serial_no='Serial no',
            sla_type='Sla type',
            status=models_support.SupportStatus.new.id,
            supplier='Supplier',
            support_type=support_utils.SupportTypeFactory().id,
        )

    def _check_supports_assets(self, support, expected_assets):
        self.assertEqual(
            len(support.assets.all()), len(expected_assets),
        )
        del self.new_support_data['assets']

    def _update_with_supports(self, _dict):
        assets = [
            assets_utils.DCAssetFactory().id,
            assets_utils.BOAssetFactory().id,
        ]
        assets_values = '|{}|'.format('|'.join(map(str, assets)))
        _dict.update(dict(assets=assets_values))
        return assets

    def test_add_support(self):
        """
        Add support with all fields filled.

        - send the full support's data with post request
        - get saved support from db
        - asserts all db support's fields with request's data
        """
        request_data = self.support_data.copy()
        response = self.client.post(reverse('add_support'), request_data)
        self.assertRedirects(
            response, reverse('support_list'), status_code=302,
            target_status_code=200,
        )
        support = models_support.Support.objects.reverse()[0]
        check_fields(self, request_data.items(), support)

    def test_edit_support(self):
        """
        Edit support with all fields filled.
        - generate support data
        - create support
        - send data via edit request to
        - get from db
        - assert data is the same as data
        """

        self.new_support_data = self.support_data.copy()
        assets = self._update_with_supports(self.new_support_data)
        support = support_utils.BOSupportFactory()
        url = reverse('edit_support', kwargs={
            'mode': 'back_office',
            'support_id': support.id,
        })
        response = self.client.post(url, self.new_support_data)
        self.assertRedirects(
            response, url, status_code=302, target_status_code=200,
        )
        support = models_support.Support.objects.get(pk=support.id)
        self._check_supports_assets(support, assets)
        check_fields(self, self.new_support_data.items(), support)


class DeviceEditViewTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.asset_src = AssetFactory(sn='123-456-789')
        self.asset_dest = AssetFactory(sn='987-832-668')

        self.model = AssetModelFactory()
        self.warehouse = WarehouseFactory()

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


class LookupsTest(TestCase):

    def test_unlogged_user_lookup_permission(self):
        """
        - send request
        - check for 403
        """
        url = (
            "/admin/lookups/ajax_lookup/"
            "KFZyYWxwaF9hc3NldHMubW9kZWxzClZCT0Fzc2V0TW9kZWxMb29rdXAKdHAxCi4="
            "?term=test"
        )
        client = Client()
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_logged_user_lookup_permission(self):
        """
        - sign in
        - send request
        - check for 200
        """
        self.client = login_as_su()
        url = (
            "/admin/lookups/ajax_lookup/"
            "KFZyYWxwaF9hc3NldHMubW9kZWxzClZCT0Fzc2V0TW9kZWxMb29rdXAKdHAxCi4="
            "?term=test"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ACLInheritanceTest(TestCase):

    def test_all_views_inherits_acls(self):
        """
        - get all views from url.py except these urls:
            - api (until it clarifies)
            - redirections
        - assert if each view has ACLClass in mro
        """
        from ralph_assets import urls
        from ralph_assets.views.base import ACLGateway
        excluded_urls_by_regexp = [
            '^api/'  # skip it until api authen./author. is resolved
        ]
        for urlpattern in urls.urlpatterns:
            if urlpattern._regex in excluded_urls_by_regexp:
                continue
            elif urlpattern.callback.func_name == 'RedirectView':
                continue
            module_name = urlpattern._callback.__module__
            class_name = urlpattern._callback.__name__
            imported_module = __import__(module_name, fromlist=[class_name])
            found_class = getattr(imported_module, class_name)
            msg = "View '{}' doesn't inherit from acl class".format(
                '.'.join([module_name, class_name])
            )
            self.assertIn(ACLGateway, found_class.__mro__, msg)


class TestImport(TestCase):
    def setUp(self):
        self.client = login_as_su()
        self.url = reverse('xls_upload')

    def _update_asset_by_csv(self, asset, field, value):
        self.client.get(self.url)
        csv_data = '"id","{}"\n"{}","{}"'.format(field, asset.id, value)

        step1_post = {
            'upload-asset_type': models_sam.AssetType.back_office.id,
            'upload-model': 'ralph_assets.asset',
            'upload-file': SimpleUploadedFile('test.csv', csv_data),
            'xls_upload_view-current_step': 'upload',
        }
        response = self.client.post(self.url, step1_post)
        self.assertContains(response, 'column_choice')
        self.assertContains(response, 'step 2/3')

        step2_post = {
            'column_choice-%s' % field: field,
            'xls_upload_view-current_step': 'column_choice',
        }
        response = self.client.post(self.url, step2_post)
        self.assertContains(response, 'step 3/3')

        step3_post = {
            'xls_upload_view-current_step': 'confirm',
        }
        response = self.client.post(self.url, step3_post)
        self.assertContains(response, 'Import done')

    def test_import_csv_asset_back_office_update(self):
        self.client.get(self.url)
        asset = BOAssetFactory()

        for field in [
            'barcode', 'invoice_no', 'order_no', 'sn', 'remarks', 'niw'
        ]:
            new_value = str(uuid.uuid1())
            self._update_asset_by_csv(asset, field, new_value)
            updated_asset = models_assets.Asset.objects.get(id=asset.id)
            self.assertEqual(
                getattr(updated_asset, field), new_value
            )
