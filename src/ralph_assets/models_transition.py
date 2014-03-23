#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    Named,
    TimeTrackable,
    WithConcurrentGetOrCreate,
)

from ralph_assets.models_assets import Asset, AssetStatus


class Action(Named):
    """
    Actions performed in the transaction
    """


class Transition(Named, TimeTrackable, WithConcurrentGetOrCreate):
    slug = models.SlugField(max_length=100, unique=True, blank=False)
    from_status = models.PositiveSmallIntegerField(
        verbose_name=_("from"),
        choices=AssetStatus(),
        null=True,
        blank=True,
    )
    to_status = models.PositiveSmallIntegerField(
        verbose_name=_("to"),
        choices=AssetStatus(),
    )
    actions = models.ManyToManyField(Action)
    report_filename = models.CharField(max_length=256, null=True, blank=True)

    def actions_names(self, *args, **kwargs):
        return [action.name for action in self.actions.all()]


class TransitionsHistory(TimeTrackable, WithConcurrentGetOrCreate):
    transition = models.ForeignKey(Transition)
    assets = models.ManyToManyField(Asset)
    logged_user = models.ForeignKey(User, related_name='logged user')
    affected_user = models.ForeignKey(User, related_name='affected user')

    def __unicode__(self, *args, **kwargs):
        return "{} - {}".format(self.transition, self.affected_user)

    @classmethod
    def create(cls, base_args):
        transition_history = TransitionsHistory(**base_args)
        transition_history.save()
