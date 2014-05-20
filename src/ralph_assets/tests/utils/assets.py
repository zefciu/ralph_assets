# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from factory import Sequence
from factory.django import DjangoModelFactory as Factory

from ralph_assets.models_assets import (
    AssetManufacturer,
    AssetOwner,
    Service,
)


class AssetManufacturerFactory(Factory):
    FACTORY_FOR = AssetManufacturer

    name = Sequence(lambda n: 'asset manufacturer #%s' % n)


class ServiceFactory(Factory):
    FACTORY_FOR = Service

    name = Sequence(lambda n: 'service #%s' % n)


class AssetOwnerFactory(Factory):
    FACTORY_FOR = AssetOwner

    name = Sequence(lambda n: 'asset owner #%s' % n)
