# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from factory.django import DjangoModelFactory as Factory

from ralph_assets.models_assets import AssetStatus
from ralph_assets.models_transition import Transition


class TransitionFactory(Factory):
    """Actions in transition must by added manually in tests"""

    FACTORY_FOR = Transition

    name = 'change-hostname'
    slug = 'change-hostname'
    to_status = AssetStatus.in_progress
    required_report = False
