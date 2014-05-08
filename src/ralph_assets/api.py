#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from django.conf import settings
from django.contrib.auth.models import User
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle

from ralph_assets.models import Asset, Licence
from ralph_assets.models_assets import (
    AssetType,
    AssetStatus,
    AssetSource,
)

THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFRAME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']
SAVE_PRIORITY = 10


class ChoicesField(fields.ApiField):
    """A Field to convert lck.django.choices.Choices field int representation
    to human readable version"""

    def __init__(self, choices_class, field_name=None, *args, **kwargs):
        self.choices_class = choices_class
        self.field_name = field_name
        super(ChoicesField, self).__init__(*args, **kwargs)

    def dehydrate(self, bundle, **kwargs):
        field_name = self.field_name if self.field_name else self.instance_name
        field_value = getattr(bundle.obj, field_name)
        return self.choices_class.from_id(field_value).name


class AssetsField(fields.RelatedField):
    """A field representing a assigned assets to user.
    Filtered by Asset.owner fiedl"""

    is_m2m = True

    def __init__(self, *args, **kwargs):
        args = (
            'ralph_assets.api.AssetsResource',
            self.get_attribute_name(),
        )
        super(AssetsField, self).__init__(*args, **kwargs)

    def dehydrate(self, bundle, **kwargs):
        assets = Asset.objects.filter(owner=bundle.obj)
        result = []
        for asset in assets:
            result.append(self.dehydrate_related(
                bundle, self.get_related_resource(asset)
            ))
        return result

    def get_attribute_name(self):
        return 'assets'


class LicenceResource(ModelResource):
    asset_type = ChoicesField(AssetType)

    class Meta:
        queryset = Licence.objects.all()
        authentication = ApiKeyAuthentication()


class AssetsResource(ModelResource):
    licences = fields.ToManyField(
        LicenceResource,
        'licence_set',
        full=True,
    )
    asset_type = ChoicesField(AssetType, 'type')
    status = ChoicesField(AssetStatus)
    source = ChoicesField(AssetSource)
    model = fields.CharField(attribute="model")
    manufacturer = fields.CharField(attribute="model__manufacturer")

    class Meta:
        queryset = Asset.objects.all()
        authentication = ApiKeyAuthentication()


class UserAssignmentsResource(ModelResource):
    is_m2m = True
    licences = fields.ToManyField(
        LicenceResource,
        'licence_set',
        full=True,
    )
    assets = AssetsField(AssetsResource, full=True)
    # Workaround to filter by username. Username is reserved to authentication
    # api user.
    user_username = fields.CharField(attribute="username")

    class Meta:
        queryset = User.objects.all()
        resource_name = 'user_assignments'
        authentication = ApiKeyAuthentication()
        excludes = [
            'username', 'password', 'date_joined', 'is_staff', 'is_superuser',
        ]
        filtering = {
            'user_username': ALL,
        }
        list_allowed_methods = ['get']
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
