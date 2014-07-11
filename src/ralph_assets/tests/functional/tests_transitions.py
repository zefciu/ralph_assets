# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib

from dj.choices import Country
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from ralph.ui.tests.global_utils import login_as_su
from ralph_assets.models_assets import Asset
from ralph_assets.models_transition import Action
from ralph_assets.tests.utils.assets import BOAssetFactory
from ralph_assets.tests.utils.transitions import TransitionFactory


ASSETS_TRANSITIONS = {
    'ENABLE': True,
    'SLUGS': {
        'RELEASE-ASSET': 'release-asset',
        'LOAN-ASSET': 'loan-asset',
        'RETURN-ASSET': 'return-asset',
        'CHANGE-HOSTNAME': 'change-hostname',
    }
}


@override_settings(ASSETS_AUTO_ASSIGN_HOSTNAME=True)
@override_settings(ASSETS_TRANSITIONS=ASSETS_TRANSITIONS)
class TestTransitionHostname(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.prepare_transition()

    def prepare_transition(self):
        self.transition = TransitionFactory()
        self.transition.actions.add(Action.objects.get(name='change_hostname'))

    def test_change_hostname_success(self):
        asset = BOAssetFactory(**{
            'hostname': '',
            'model__category__code': 'PC'
        })
        post_data = {'country': Country.pl.id}
        url_base = reverse('transition', args=('back_office',))
        url_params = {'select': asset.id, 'transition_type': 'change-hostname'}
        url = "{}?{}".format(url_base, urllib.urlencode(url_params))
        self.client.post(url, post_data, follow=True)
        changed_asset = Asset.objects.get(pk=asset.id)
        self.assertEqual(changed_asset.hostname, 'POLPC00001')
