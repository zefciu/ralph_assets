# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from ralph_assets.views.asset import DeleteAsset, HistoryAsset, BulkEdit
from ralph_assets.views.ajax import CategoryDependencyView, ModelDependencyView
from ralph_assets.views.attachment import AddAttachment, DeleteAttachment
from ralph_assets.views.base import AssetsBase, DataTableColumnAssets, get_return_link
from ralph_assets.views.device import AddDevice, EditDevice, SplitDeviceView
from ralph_assets.views.part import AddPart, EditPart
from ralph_assets.views.sam import (
    SoftwareCategoryNameColumn,
    LicenceLinkColumn,
    SoftwareCategoryList,
    LicenceList,
    AddLicence,
    EditLicence,
    DeleteLicence,
    HistoryLicence,
)
from ralph_assets.views.search import (
    AssetsSearchQueryableMixin,
    AssetSearch,
    GenericSearch,
)
from ralph_assets.views.user import EditUser, UserDetails, UserList

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


# # TODO: zamienić na reverse('asset_search', args=(mode,))
# def _get_return_link(mode):
#     return "/assets/%s/" % mode
