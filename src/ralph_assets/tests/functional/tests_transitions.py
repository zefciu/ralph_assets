# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib

import django.dispatch
from dj.choices import Country
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from ralph.ui.tests.global_utils import login_as_su
from ralph_assets import signals
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
        self.asset = BOAssetFactory(**{
            'hostname': '',
            'model__category__code': 'PC',
        })
        self.post_data = {'country': Country.pl.id}
        self.url_base = reverse('transition', args=('back_office',))
        self.url_params = {
            'select': self.asset.id,
            'transition_type': 'change-hostname',
        }
        self.url = "{}?{}".format(
            self.url_base, urllib.urlencode(self.url_params)
        )
        self.prepare_transition()

    def prepare_transition(self):
        self.transition = TransitionFactory()
        self.transition.actions.add(Action.objects.get(name='change_hostname'))

    def test_change_hostname_success(self):
        self.client.post(self.url, self.post_data, follow=True)
        changed_asset = Asset.objects.get(pk=self.asset.id)
        self.assertEqual(changed_asset.hostname, 'POLPC00001')

    def test_successful_post_transition(self):
        """
        Transition is done successfully.
        """
        @django.dispatch.receiver(signals.post_transition)
        def post_transition_handler(sender, user, assets, **kwargs):
            pass

        response = self.client.post(self.url, self.post_data, follow=True)
        self.assertEqual(len(response.context['messages']), 1)
        self.assertEqual(
            str(response.context['messages']._loaded_messages[0]),
            "Transitions performed successfully",
        )

    def test_failed_post_transition(self):
        """
        Transition is done unsuccessfully.
        """
        @django.dispatch.receiver(signals.post_transition)
        def post_transition_handler(sender, user, assets, **kwargs):
            from ralph_assets.views import transition
            raise transition.PostTransitionException(
                "Unable to generate document - try later, please."
            )

        response = self.client.post(self.url, self.post_data, follow=True)
        self.assertEqual(len(response.context['messages']), 1)
        self.assertEqual(
            str(response.context['messages']._loaded_messages[0]),
            "Unable to generate document - try later, please.",
        )
