#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.utils.translation import ugettext_lazy as _


class HistoryManager(models.Manager):
    def get_history_for_this_object(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return self.get_history_for_this_content_type(
            content_type=content_type,
            object_id=obj.id
        )

    def get_history_for_this_content_type(self, content_type, object_id):
        return self.model.objects.filter(
            content_type=content_type,
            object_id=object_id,
        )

    def log_changes(self, obj, diff_data):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        changed_items = []

        for data in diff_data:
            changed_items.append(
                self.model(
                    content_type=content_type,
                    object_id=obj.id,
                    field_name=data['field'],
                    old_value=data['old'] if data['old'] else '-',
                    new_value=data['new'] if data['new'] else '-',
                )
            )
        self.model.objects.bulk_create(changed_items)


class History(models.Model):
    date = models.DateTimeField(verbose_name=_('date'), default=datetime.now)
    user = models.ForeignKey(
        'auth.User', verbose_name=_('user'), null=True,
        blank=True, default=None, on_delete=models.SET_NULL
    )
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    field_name = models.CharField(max_length=64, default='')
    old_value = models.CharField(max_length=255, default='')
    new_value = models.CharField(max_length=255, default='')
    objects = HistoryManager()

    class Meta:
        app_label = 'ralph_assets'
        verbose_name = _('history change')
        verbose_name_plural = _('history changes')

    @classmethod
    def get_history_url_for_object(cls, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return reverse('history_for_model', kwargs={
            'content_type': content_type.id,
            'object_id': obj.id,
        })
