# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from ralph_assets.models import Asset
from ralph_assets.models_history import AssetHistoryChange
from ralph_assets.models_assets import AssetType
from ralph_assets.views.base import AssetsBase, BulkEditBase, get_return_link
from ralph_assets.views.search import _AssetSearch, AssetSearchDataTable
from ralph_assets.views.utils import _move_data, _update_office_info
from ralph.util.reports import Report


MAX_PAGE_SIZE = 65535
HISTORY_PAGE_SIZE = 25


logger = logging.getLogger(__name__)


class DeleteAsset(AssetsBase):

    def post(self, *args, **kwargs):
        record_id = self.request.POST.get('record_id')
        try:
            self.asset = Asset.objects.get(
                pk=record_id
            )
        except Asset.DoesNotExist:
            messages.error(
                self.request, _("Selected asset doesn't exists.")
            )
            return HttpResponseRedirect(get_return_link(self.mode))
        else:
            if self.asset.type < AssetType.BO:
                self.back_to = '/assets/dc/'
            else:
                self.back_to = '/assets/back_office/'
            if self.asset.has_parts():
                parts = self.asset.get_parts_info()
                messages.error(
                    self.request,
                    _("Cannot remove asset with parts assigned. Please remove "
                        "or unassign them from device first. ".format(
                            self.asset,
                            ", ".join([str(part.asset) for part in parts])
                        ))
                )
                return HttpResponseRedirect(
                    '{}{}{}'.format(
                        self.back_to, 'edit/device/', self.asset.id,
                    )
                )
            # changed from softdelete to real-delete, because of
            # key-constraints issues (sn/barcode) - to be resolved.
            self.asset.delete_with_info()
            return HttpResponseRedirect(self.back_to)


class HistoryAsset(AssetsBase):
    template_name = 'assets/history.html'

    def get_context_data(self, **kwargs):
        query_variable_name = 'history_page'
        ret = super(HistoryAsset, self).get_context_data(**kwargs)
        asset_id = kwargs.get('asset_id')
        asset = Asset.admin_objects.get(id=asset_id)
        history = AssetHistoryChange.objects.filter(
            Q(asset_id=asset.id) |
            Q(device_info_id=getattr(asset.device_info, 'id', 0)) |
            Q(part_info_id=getattr(asset.part_info, 'id', 0)) |
            Q(office_info_id=getattr(asset.office_info, 'id', 0))
        ).order_by('-date')
        status = bool(self.request.GET.get('status', ''))
        if status:
            history = history.filter(field_name__exact='status')
        try:
            page = int(self.request.GET.get(query_variable_name, 1))
        except ValueError:
            page = 1
        if page == 0:
            page = 1
            page_size = MAX_PAGE_SIZE
        else:
            page_size = HISTORY_PAGE_SIZE
        history_page = Paginator(history, page_size).page(page)
        if asset.get_data_type() == 'device':
            url_name = 'device_edit'
        else:
            url_name = 'part_edit'
        object_url = reverse(
            url_name, kwargs={'asset_id': asset.id, 'mode': self.mode},
        )
        ret.update({
            'history': history,
            'history_page': history_page,
            'status': status,
            'query_variable_name': query_variable_name,
            'object': asset,
            'object_url': object_url,
            'title': _('History asset'),
            'show_status_button': True,
        })
        return ret


class AssetSearch(Report, AssetSearchDataTable):
    """The main-screen search form for all type of assets."""


class AssetBulkEdit(BulkEditBase, _AssetSearch):
    model = Asset
    commit_on_valid = False

    def initial_forms(self, formset, queryset):
        for idx, asset in enumerate(queryset):
            if asset.office_info:
                for field in ['purpose']:
                    if field not in formset.forms[idx].fields:
                        continue
                    formset.forms[idx].fields[field].initial = (
                        getattr(asset.office_info, field, None)
                    )

    def save_formset(self, instances, formset):
        with transaction.commit_on_success():
            for idx, instance in enumerate(instances):
                instance.modified_by = self.request.user.get_profile()
                instance.save(user=self.request.user)
                new_src, office_info_data = _move_data(
                    formset.forms[idx].cleaned_data,
                    {}, ['purpose']
                )
                formset.forms[idx].cleaned_data = new_src
                instance = _update_office_info(
                    self.request.user, instance,
                    office_info_data,
                )

    def handle_formset_error(self, formset_error):
        messages.error(
            self.request,
            _(('Please correct errors and check both "serial numbers" and '
               '"barcodes" for duplicates'))
        )
