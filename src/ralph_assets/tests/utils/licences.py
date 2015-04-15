# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from decimal import Decimal
from random import randint, randrange
import datetime
import itertools

from factory import (
    fuzzy,
    Sequence,
    SubFactory,
    lazy_attribute,
    post_generation,
)
from factory.django import DjangoModelFactory
from ralph.account.models import Region

from ralph_assets.models_assets import AssetType
from ralph_assets.licences.models import (
    Licence,
    LicenceAsset,
    LicenceUser,
    LicenceType,
    SoftwareCategory,
)
from ralph_assets.tests.utils.assets import (
    unique_str,
    AssetFactory,
    AssetManufacturerFactory,
    AssetOwnerFactory,
    BudgetInfoFactory,
    ServiceFactory,
    UserFactory,
)

licence_type_generator = itertools.cycle([
    'per processor', 'per user', 'OEM'
])
software_category_generator = itertools.cycle([
    'Database', 'Office software', 'Free software', 'Other'
])


class LicenceTypeFactory(DjangoModelFactory):
    FACTORY_FOR = LicenceType
    FACTORY_DJANGO_GET_OR_CREATE = ('name', )

    @lazy_attribute
    def name(self):
        return licence_type_generator.next()


class SoftwareCategoryFactory(DjangoModelFactory):
    FACTORY_FOR = SoftwareCategory
    FACTORY_DJANGO_GET_OR_CREATE = ('name', )

    asset_type = AssetType.BO

    @lazy_attribute
    def name(self):
        return software_category_generator.next()


class LicenceFactory(DjangoModelFactory):
    FACTORY_FOR = Licence

    asset_type = AssetType.back_office.id
    # assets: probabbly it should be set as kwargs during creation?
    budget_info = SubFactory(BudgetInfoFactory)
    invoice_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    invoice_no = Sequence(lambda n: 'INVOICE-NUMBER-%s' % n)
    licence_type = SubFactory(LicenceTypeFactory)
    license_details = Sequence(lambda n: 'Licence-details-%s' % n)
    manufacturer = SubFactory(AssetManufacturerFactory)
    order_no = Sequence(lambda n: 'ORDER-NUMBER-%s' % n)
    parent = None
    property_of = SubFactory(AssetOwnerFactory)
    provider = Sequence(lambda n: 'provider-{}'.format(n))
    remarks = Sequence(lambda n: 'remarks-{}'.format(n))
    service_name = SubFactory(ServiceFactory)
    software_category = SubFactory(SoftwareCategoryFactory)
    users = None
    valid_thru = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))

    @lazy_attribute
    def accounting_id(self):
        return str(randint(1, 100))

    @lazy_attribute
    def niw(self):
        return str(unique_str())

    @lazy_attribute
    def number_bought(self):
        return randint(1, 100)

    @lazy_attribute
    def price(self):
        return Decimal(randrange(10000)) / 100

    @lazy_attribute
    def region(self):
        # lazy attr because static fails (it's not accessible during import)
        return Region.get_default_region()

    @lazy_attribute
    def sn(self):
        return str(unique_str())

    @post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return None
        return [UserFactory() for i in range(randint(1, 8))]


class LicenceAssetFactory(DjangoModelFactory):
    FACTORY_FOR = LicenceAsset
    licence = SubFactory(LicenceFactory)
    asset = SubFactory(AssetFactory)
    quantity = 1


class LicenceUserFactory(DjangoModelFactory):
    FACTORY_FOR = LicenceUser
    licence = SubFactory(LicenceFactory)
    user = SubFactory(UserFactory)
    quantity = 1
