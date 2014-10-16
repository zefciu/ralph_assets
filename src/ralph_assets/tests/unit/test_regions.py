# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock
from django.test import TestCase
from ralph.util.tests.utils import (
    RegionFactory,
)

from ralph_assets.licences.models import Licence
from ralph_assets.models_support import Support
from ralph_assets.tests.utils.licences import LicenceFactory
from ralph_assets.tests.utils.supports import DCSupportFactory


class BaseRegions(object):

    model_class = None
    model_factory = None

    @mock.patch('ralph.middleware.get_actual_regions')
    def test_db_manger_shows_region(self, mocked_method):
        polish_region = RegionFactory(name='PL')
        dutch_region = RegionFactory(name='NL')
        self.model_factory(region=polish_region)
        self.model_factory(region=dutch_region)

        mocked_method.side_effect = lambda: [polish_region, dutch_region]

        self.assertEqual(self.model_class.objects.count(), 2)
        self.assertEqual(self.model_class.admin_objects.count(), 2)

    @mock.patch('ralph.middleware.get_actual_regions')
    def test_db_manger_shows_regions(self, mocked_method):
        polish_region = RegionFactory(name='PL')
        dutch_region = RegionFactory(name='NL')
        self.model_factory(region=polish_region)
        self.model_factory(region=dutch_region)

        mocked_method.side_effect = lambda: [dutch_region]

        self.assertEqual(self.model_class.objects.count(), 1)
        self.model_factory(region=dutch_region)
        self.assertEqual(self.model_class.objects.count(), 2)
        self.assertEqual(self.model_class.admin_objects.count(), 3)


class TestLicenceRegions(BaseRegions, TestCase):

    model_class = Licence
    model_factory = LicenceFactory


class TestSupport(BaseRegions, TestCase):

    model_class = Support
    model_factory = DCSupportFactory
