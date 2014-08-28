# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from ralph_assets.history.views import (
    HistoryListForModel
)

urlpatterns = patterns(
    '',
    url(
        (r'^(?P<content_type>[-\d]+)/(?P<object_id>[-\d]+)/$'),
        HistoryListForModel.as_view(),
        name='history_for_model',
    ),
    # url(
    #     _(r'^abuses/(?P<pk>[-\d]+)/$'),
    #     AbuseDetail.as_view(),
    #     name='abuse_detail'
    # ),
    # url(
    #     _(r'^abuses/(?P<pk>[-\d]+)/change_state/$'),
    #     AbuseChangeState.as_view(),
    #     name='abuse_change_state'
    # ),
    # url(
    #     _(r'^abuses/create/(?P<content_type>[-\d]+)/(?P<object_id>[-\d]+)/$'),
    #     AbuseCreate.as_view(),
    #     name='abuse_create'
    # ),
)
