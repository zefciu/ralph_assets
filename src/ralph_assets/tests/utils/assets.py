# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from factory import Sequence, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory as Factory
from random import randint
from uuid import uuid1

# TODO: ralph DeviceFactory
# from ralph.discovery.models_device import Device, DeviceType

from django.template.defaultfilters import slugify

from ralph_assets.models_assets import (
    Asset,
    AssetCategory,
    AssetCategoryType,
    AssetManufacturer,
    AssetModel,
    AssetOwner,
    AssetStatus,
    AssetSource,
    AssetType,
    Service,
    DeviceInfo,
    Warehouse,
)


class ServiceFactory(Factory):
    FACTORY_FOR = Service

    name = Sequence(lambda n: 'service #%s' % n)


class AssetOwnerFactory(Factory):
    FACTORY_FOR = AssetOwner

    name = Sequence(lambda n: 'asset owner #%s' % n)


class AssetCategoryFactory(Factory):
    FACTORY_FOR = AssetCategory

    name = Sequence(lambda n: 'asset category #%s' % n)
    type = AssetCategoryType.back_office

    @lazy_attribute
    def slug(self):
        return slugify(str(self.type) + self.name)


class AssetSubCategoryFactory(AssetCategoryFactory):
    parent = SubFactory(AssetCategoryFactory)


class AssetManufacturerFactory(Factory):
    FACTORY_FOR = AssetManufacturer

    name = Sequence(lambda n: 'Manufacturer #%s' % n)


class AssetModelFactory(Factory):
    FACTORY_FOR = AssetModel

    name = Sequence(lambda n: 'Model #%s' % n)
    type = AssetCategoryType.back_office
    manufacturer = SubFactory(AssetManufacturerFactory)


class WarehouseFactory(Factory):
    FACTORY_FOR = Warehouse

    name = Sequence(lambda n: 'Warehouse #%s' % n)


class DeviceInfoFactory(Factory):
    FACTORY_FOR = DeviceInfo

    ralph_device_id = Sequence(lambda n: n)
    u_level = randint(0, 100)
    u_height = randint(0, 100)
    rack = Sequence(lambda n: 'Rack #%s' % n)


class AssetFactory(Factory):
    FACTORY_FOR = Asset

    type = AssetType.data_center
    model = SubFactory(AssetModelFactory)
    status = AssetStatus.new
    source = AssetSource.shipment
    model = SubFactory(AssetModelFactory)
    warehouse = SubFactory(WarehouseFactory)
    device_info = SubFactory(DeviceInfoFactory)
    support_period = 24
    support_type = 'standard'

    @lazy_attribute
    def sn(self):
        return str(uuid1())
