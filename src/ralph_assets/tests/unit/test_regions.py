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

from ralph_assets.licences.models import (
    Licence,
)
from ralph_assets.tests.utils.licences import LicenceFactory


class TestLicenceRegions(TestCase):

    def setUp(self):
        pass

    @mock.patch('ralph.middleware.get_actual_regions')
    def test_db_manger_shows_region(self, mocked_method):
        polish_region = RegionFactory(name='PL')
        dutch_region = RegionFactory(name='NL')
        LicenceFactory(region=polish_region)
        LicenceFactory(region=dutch_region)

        mocked_method.side_effect = lambda: [polish_region, dutch_region]

        self.assertEqual(Licence.objects.count(), 2)
        self.assertEqual(Licence.admin_objects.count(), 2)

    @mock.patch('ralph.middleware.get_actual_regions')
    def test_db_manger_shows_regions(self, mocked_method):
        polish_region = RegionFactory(name='PL')
        dutch_region = RegionFactory(name='NL')
        LicenceFactory(region=polish_region)
        LicenceFactory(region=dutch_region)

        mocked_method.side_effect = lambda: [dutch_region]

        self.assertEqual(Licence.objects.count(), 1)
        LicenceFactory(region=dutch_region)
        self.assertEqual(Licence.objects.count(), 2)
        self.assertEqual(Licence.admin_objects.count(), 3)
