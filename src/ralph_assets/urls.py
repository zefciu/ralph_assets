# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView

from ralph_assets.views import (
    AddDevice,
    AddPart,
    BulkEdit,
    SplitDeviceView,
    EditDevice,
    EditPart,
    AssetSearch,
    DeleteAsset,
    HistoryAsset,
    XlsUploadView,
)

from ralph_assets.forms import XLS_UPLOAD_FORMS


urlpatterns = patterns(
    '',
    url(r'^$',
        RedirectView.as_view(url='/assets/dc/search'),
        name='dc'),
    url(r'dc/$', RedirectView.as_view(url='/assets/dc/search'),
        name='dc'),
    url(r'back_office/$',
        RedirectView.as_view(url='/assets/back_office/search'),
        name='dc'),

    url(r'(?P<mode>(back_office|dc))/search',
        login_required(AssetSearch.as_view()),
        name='dc'),
    url(r'(?P<mode>(back_office|dc))/add/device/',
        login_required(AddDevice.as_view()),
        name='dc'),
    url(r'(?P<mode>(back_office|dc))/add/part/',
        login_required(AddPart.as_view()),
        name='dc'),
    url(r'(?P<mode>(back_office|dc))/edit/device/(?P<asset_id>[0-9]+)/$',
        login_required(EditDevice.as_view()),
        name='device_edit'),
    url(r'(?P<mode>(back_office|dc))/edit/part/(?P<asset_id>[0-9]+)/$',
        login_required(EditPart.as_view()),
        name='dc'),
    url(r'(?P<mode>(back_office|dc))/history/device/(?P<asset_id>[0-9]+)/$',
        login_required(HistoryAsset.as_view()),
        name='device_history'),
    url(r'(?P<mode>(back_office|dc))/history/part/(?P<asset_id>[0-9]+)/$',
        login_required(HistoryAsset.as_view()),
        name='part_history'),
    url(r'(?P<mode>(back_office|dc))/bulkedit/$',
        login_required(BulkEdit.as_view()),
        name='dc'),
    url(r'(?P<mode>(back_office|dc))/delete/asset/$',
        login_required(DeleteAsset.as_view()),
        name='dc'),
    url(r'(?P<mode>(back_office|dc))/split/asset/(?P<asset_id>[0-9]+)/$',
        login_required(SplitDeviceView.as_view()),
        name='device_split'),
    url(
        r'xls/$',
        login_required(XlsUploadView.as_view(XLS_UPLOAD_FORMS)),
        name='xls_upload',
    ),
)
