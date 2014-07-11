# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from factory import (
    fuzzy,
    Sequence,
    SubFactory,
    lazy_attribute,
    post_generation,
)
from factory.django import DjangoModelFactory as Factory
from random import randint
from uuid import uuid1

from ralph_assets.models_assets import AssetType, AssetStatus
from ralph_assets.models_transition import Transition

from ralph_assets.tests.utils.assets import (
    AssetManufacturerFactory,
    AssetOwnerFactory,
    BudgetInfoFactory,
    ServiceFactory,
    UserFactory,
)


class TransitionFactory(Factory):
    """Actions in transition must by added manually in tests"""

    FACTORY_FOR = Transition

    name = 'change-hostname'
    slug = 'change-hostname'
    to_status = AssetStatus.in_progress
    required_report = False



