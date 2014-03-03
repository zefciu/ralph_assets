# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from random import randint

from ralph_assets.models_assets import (
    Asset,
    AssetCategory,
    AssetCategoryType,
    AssetModel,
    AssetSource,
    AssetStatus,
    AssetType,
    AssetManufacturer,
    DeviceInfo,
    Warehouse
)

DEFAULT_ASSET_DATA = dict(
    manufacturer='Manufacturer1',
    model='Model1',
    power_consumption=100,
    height_of_device='D4',
    warehouse='Warehouse',
    type=AssetType.data_center,
    status=AssetStatus.new,
    source=AssetSource.shipment,
    category='Category1',
)

SCREEN_ERROR_MESSAGES = dict(
    duplicated_sn_or_bc='Please correct duplicated serial numbers or barcodes.',  # noqa
    duplicated_sn_in_field='There are duplicate serial numbers in field.',
    contain_white_character="Serial number can't contain white characters.",
    django_required='This field is required.',
    count_sn_and_bc='Barcode list could be empty or must have the same number '
                    'of items as a SN list.',
    barcode_already_exist='Following barcodes already exists in DB: '
)


def create_manufacturer(name=DEFAULT_ASSET_DATA['manufacturer']):
    manufacturer, created = AssetManufacturer.objects.get_or_create(name=name)
    return manufacturer


def create_warehouse(name=DEFAULT_ASSET_DATA['warehouse']):
    warehouse, created = Warehouse.objects.get_or_create(name=name)
    return warehouse


def create_model(name=DEFAULT_ASSET_DATA['model'], manufacturer=None):
    """name = string, manufacturer = string"""
    if not manufacturer:
        manufacturer = create_manufacturer()
    else:
        manufacturer = create_manufacturer(manufacturer)
    model, created = AssetModel.objects.get_or_create(name=name)
    if created:
        model.manufacturer = manufacturer
        model.save()
    return model


def create_device(size=1):
    device = DeviceInfo(size=size)
    device.save()
    return device


def create_asset(sn, **kwargs):
    if not kwargs.get('type'):
        kwargs.update(type=DEFAULT_ASSET_DATA['type'])
    if not kwargs.get('model'):
        kwargs.update(model=create_model())
    if not kwargs.get('device_info'):
        kwargs.update(device_info=create_device())
    if not kwargs.get('status'):
        kwargs.update(status=DEFAULT_ASSET_DATA['status'])
    if not kwargs.get('source'):
        kwargs.update(source=DEFAULT_ASSET_DATA['source'])
    if not kwargs.get('support_period'):
        kwargs.update(support_period=24)
    if not kwargs.get('support_type'):
        kwargs.update(support_type='standard')
    if not kwargs.get('warehouse'):
        kwargs.update(warehouse=create_warehouse())
    kwargs.update(sn=sn)
    asset = Asset(**kwargs)
    asset.save()
    return asset


def create_category(type='data_center', name=DEFAULT_ASSET_DATA['category']):
    if type == 'back_office':
        type = AssetCategoryType.back_office
    elif type == 'data_center':
        type = AssetCategoryType.data_center
    category = AssetCategory()
    category.name = name
    category.type = type
    category.save()
    subcategory = AssetCategory()
    subcategory.name = 'Subcategory'
    subcategory.type = type
    subcategory.parent = category
    subcategory.save()
    return subcategory

def get_bulk_edit_post_data_part(*args, **kwargs):
    id = kwargs.get('id')

    model_id = kwargs.get('model')
    if model_id is None:
        model = create_model()
        model_id = model.id

    sn = kwargs.get('sn')
    if sn is None:
        sn = '-'.join([str(randint(1000, 9999)) for i in xrange(4)])

    barcode = kwargs.get('barcode')
    if barcode is None:
        barcode = 'bc-{0}'.format(str(randint(1000, 9999)))

    warehouse = kwargs.get('warehouse')
    if warehouse is None:
        warehouse = create_warehouse()

    return {
        'form-{0}-id'.format(id-1): id,
        'form-{0}-type'.format(id-1):\
            kwargs.get('type', AssetType.data_center.id),
        'form-{0}-model'.format(id-1): model_id,
        'form-{0}-invoice_no'.format(id-1):\
            kwargs.get('invoice_no', 'Invoice No0'),
        'form-{0}-invoice_date'.format(id-1):\
            kwargs.get('invoice_date', '2014-01-01'),
        'form-{0}-order_no'.format(id-1):\
            kwargs.get('order_no', 'Order No0'),
        'form-{0}-sn'.format(id-1): sn,
        'form-{0}-barcode'.format(id-1): barcode,
        'form-{0}-support_period'.format(id-1):\
            kwargs.get('support_period', 24),
        'form-{0}-support_type'.format(id-1):\
            kwargs.get('support_type', 'standard0'),
        'form-{0}-support_void_reporting'.format(id-1):\
            kwargs.get('support_void_reporting', 'on'),
        'form-{0}-provider'.format(id-1):\
            kwargs.get('provider', 'Provider 0'),
        'form-{0}-status'.format(id-1):\
            kwargs.get('status', AssetStatus.in_progress.id),
        'form-{0}-source'.format(id-1):\
            kwargs.get('source', AssetSource.shipment.id),
        'form-{0}-ralph_device_id'.format(id-1):\
            kwargs.get('ralph_device_id', ''),
        'form-{0}-price'.format(id-1):\
            kwargs.get('price', 10),
        'form-{0}-warehouse'.format(id-1): warehouse.id,
    }

def get_bulk_edit_post_data(*args, **kwargs):
    post_data = {
        'form-TOTAL_FORMS': u'{0}'.format(len(args)),
        'form-INITIAL_FORMS': u'{0}'.format(len(args)),
        'form-MAX_NUM_FORMS': u'',
    }
    for i, data in enumerate(args):
        data['id'] = i + 1
        post_data.update(get_bulk_edit_post_data_part(**data))
    return post_data
