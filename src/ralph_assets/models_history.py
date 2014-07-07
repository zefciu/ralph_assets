#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models as db
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ralph_assets import models_assets
from ralph_assets.history import field_changes
from ralph_assets.models_assets import (
    Asset,
    DeviceInfo,
    PartInfo,
    OfficeInfo,
)
from ralph_assets.models_sam import Licence
from ralph_assets.models_support import Support


class AssetHistoryChange(db.Model):
    """Represent a single change of a asset."""

    date = db.DateTimeField(verbose_name=_("date"), default=datetime.now)
    asset = db.ForeignKey(
        'Asset', verbose_name=_("asset"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL
    )
    device_info = db.ForeignKey(
        'DeviceInfo', verbose_name=_("device_info"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL
    )
    part_info = db.ForeignKey(
        'PartInfo', verbose_name=_("part_info"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL
    )
    office_info = db.ForeignKey(
        'OfficeInfo', verbose_name=_("office_info"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL
    )
    user = db.ForeignKey(
        'auth.User', verbose_name=_("user"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL
    )
    field_name = db.CharField(max_length=64, default='')
    old_value = db.CharField(max_length=255, default='')
    new_value = db.CharField(max_length=255, default='')
    comment = db.TextField(null=True)

    class Meta:
        verbose_name = _("history change")
        verbose_name_plural = _("history changes")

    def __unicode__(self):
        return "{:r}.{:r} = {:r} -> {:r} by {:r} on {:r} ({:r})".format(
            self.asset, self.field_name, self.old_value, self.new_value,
            self.user, self.date, self.id
        )


class LicenceHistoryChange(db.Model):
    """Represent a single change of a Licence"""

    date = db.DateTimeField(verbose_name=_("date"), default=datetime.now)
    licence = db.ForeignKey(
        Licence,
        verbose_name=_('Licence'),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    user = db.ForeignKey(
        User,
        verbose_name=_("user"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    field_name = db.CharField(max_length=64, default='')
    old_value = db.CharField(max_length=255, default='')
    new_value = db.CharField(max_length=255, default='')

    class Meta:
        verbose_name = _("history change")
        verbose_name_plural = _("history changes")

    def __unicode__(self):
        return "{!r}.{!r} = {!r} -> {!r} by {!r} on {!r} ({!r})".format(
            self.licence,
            self.field_name,
            self.old_value,
            self.new_value,
            self.user,
            self.date,
            self.id,
        )


class SupportHistoryChange(db.Model):
    """Represent a single change of a Support"""

    date = db.DateTimeField(verbose_name=_("date"), default=datetime.now)
    support = db.ForeignKey(
        Support,
        verbose_name=_('Support'),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    user = db.ForeignKey(
        User,
        verbose_name=_("user"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    field_name = db.CharField(max_length=64, default='')
    old_value = db.CharField(max_length=255, default='')
    new_value = db.CharField(max_length=255, default='')

    class Meta:
        verbose_name = _("history change")
        verbose_name_plural = _("history changes")

    def __unicode__(self):
        return "{!r}.{!r} = {!r} -> {!r} by {!r} on {!r} ({!r})".format(
            self.support,
            self.field_name,
            self.old_value,
            self.new_value,
            self.user,
            self.date,
            self.id,
        )


@receiver(post_save, sender=Asset, dispatch_uid='ralph.history_assets')
def asset_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries when a asset changes."""
    for field, orig, new in field_changes(instance):
        AssetHistoryChange(
            asset=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
            comment=instance.save_comment,
        ).save()


@receiver(pre_save, sender=Asset, dispatch_uid='ralph_assets.views.device')
def device_hostname_assigning(sender, instance, raw, using, **kwargs):
    """A hook for assigning ``hostname`` value when an asset is edited."""
    if getattr(settings, 'ASSETS_AUTO_ASSIGN_HOSTNAME', None):
        for field, orig, new in field_changes(instance):
            status_desc = models_assets.AssetStatus.in_progress.desc
            if all((
                field == 'status', orig != status_desc, new == status_desc
            )):
                instance._try_assign_hostname(commit=False)


@receiver(post_save, sender=DeviceInfo, dispatch_uid='ralph.history_assets')
def device_info_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries
    when a DeviceInfo changes.
    """
    for field, orig, new in field_changes(instance):
        AssetHistoryChange(
            device_info=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
            comment=instance.save_comment,
        ).save()


@receiver(post_save, sender=PartInfo, dispatch_uid='ralph.history_assets')
def part_info_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries
    when a PartInfo changes.
    """
    for field, orig, new in field_changes(instance):
        AssetHistoryChange(
            part_info=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
            comment=instance.save_comment,
        ).save()


@receiver(post_save, sender=OfficeInfo, dispatch_uid='ralph.history_assets')
def office_info_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries when a Office changes."""
    for field, orig, new in field_changes(instance):
        AssetHistoryChange(
            office_info=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
            comment=instance.save_comment,
        ).save()


@receiver(post_save, sender=Licence, dispatch_uid='ralph.history_licence')
def licence_post_save(sender, instance, raw, using, **kwargs):
    for field, orig, new in field_changes(instance):
        LicenceHistoryChange(
            licence=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
        ).save()


@receiver(post_save, sender=Support)
def support_post_save(sender, instance, raw, using, **kwargs):
    for field, orig, new in field_changes(instance):
        SupportHistoryChange(
            support=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
        ).save()
