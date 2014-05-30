# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from ralph_assets.views.base import AssetsBase, DataTableColumnAssets
from ralph_assets.views.part import AddPart, EditPart
from ralph_assets.views.device import AddDevice, EditDevice, SplitDeviceView
from ralph_assets.views.user import EditUser, UserDetails, UserList
from ralph_assets.views.attachment import AddAttachment, DeleteAttachment
from ralph_assets.views.asset import DeleteAsset, HistoryAsset, BulkEdit
from ralph_assets.views.search import (
    AssetsSearchQueryableMixin,
    AssetSearch,
    GenericSearch,
)


from bob.data_table import DataTableColumn, DataTableMixin
from bob.views import DependencyView
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.forms.models import modelformset_factory, formset_factory
from django.http import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from rq import get_current_job

from ralph_assets.forms import (
    AddDeviceForm,
    AddPartForm,
    AttachmentForm,
    BackOfficeSearchAssetForm,
    BasePartForm,
    DataCenterSearchAssetForm,
    DeviceForm,
    EditPartForm,
    MoveAssetPartForm,
    OfficeForm,
    SearchUserForm,
    SplitDevice,
    UserRelationForm
)
from ralph_assets import models as assets_models
from ralph_assets.models import (
    Asset,
    AssetModel,
    AssetCategory,
    DeviceInfo,
    Licence,
    OfficeInfo,
    PartInfo,
    TransitionsHistory,
)
from ralph_assets.models_assets import (
    Attachment,
    AssetType,
    ASSET_TYPE2MODE,
)
from ralph_assets.models_history import AssetHistoryChange
from ralph.business.models import Venture
from ralph.util.api_assets import get_device_components
from ralph.util.reports import Report, set_progress

SAVE_PRIORITY = 200
MAX_BULK_EDIT_SIZE = 40
HISTORY_PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535


logger = logging.getLogger(__name__)



def _move_data(src, dst, fields):
    for field in fields:
        if field in src:
            value = src.pop(field)
            dst[field] = value
    return src, dst




def _get_return_link(mode):
    return "/assets/%s/" % mode


@transaction.commit_on_success
def _create_device(creator_profile, asset_data, cleaned_additional_info, mode):
    if mode == 'dc':
        asset = Asset(created_by=creator_profile, **asset_data)
        device_info = DeviceInfo()
        device_info.ralph_device_id = cleaned_additional_info[
            'ralph_device_id'
        ]
        device_info.u_level = cleaned_additional_info['u_level']
        device_info.u_height = cleaned_additional_info['u_height']
        device_info.save(user=creator_profile.user)
        asset.device_info = device_info
    elif mode == 'back_office':
        _move_data(asset_data, cleaned_additional_info, ['purpose'])
        asset = Asset(created_by=creator_profile, **asset_data)
        office_info = OfficeInfo()
        office_info.__dict__.update(**cleaned_additional_info)
        office_info.save(user=creator_profile.user)
        asset.office_info = office_info
    asset.save(user=creator_profile.user)
    return asset


@transaction.commit_on_success
def _update_asset(modifier_profile, asset, asset_updated_data):
    if (
        'barcode' not in asset_updated_data or
        not asset_updated_data['barcode']
    ):
        asset_updated_data['barcode'] = None
    asset_updated_data.update({'modified_by': modifier_profile})
    asset.__dict__.update(**asset_updated_data)
    return asset


class DeleteLicence(AssetsBase):
    """Delete a licence."""

    def post(self, *args, **kwargs):
        record_id = self.request.POST.get('record_id')
        try:
            licence = Licence.objects.get(pk=record_id)
        except Asset.DoesNotExist:
            messages.error(self.request, _("Selected asset doesn't exists."))
            return HttpResponseRedirect(_get_return_link(self.mode))
        self.back_to = reverse(
            'licence_list',
            kwargs={'mode': ASSET_TYPE2MODE[licence.asset_type]},
        )
        licence.delete()
        return HttpResponseRedirect(self.back_to)


class CategoryDependencyView(DependencyView):
    def get_values(self, value):
        try:
            profile = User.objects.get(pk=value).profile
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return HttpResponseBadRequest("Incorrect user id")
        values = dict(
            [(name, getattr(profile, name)) for name in (
                'location',
                'company',
                'employee_id',
                'cost_center',
                'profit_center',
                'department',
                'manager',
            )]
        )
        return values


class ModelDependencyView(DependencyView):
    def get_values(self, value):
        category = ''
        if value != '':
            try:
                category = AssetModel.objects.get(pk=value).category_id
            except (
                AssetModel.DoesNotExist,
                AssetModel.MultipleObjectsReturned,
            ):
                return HttpResponseBadRequest("Incorrect AssetModel pk")
        return {
            'category': category,
        }

