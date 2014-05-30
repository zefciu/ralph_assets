# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.forms.models import modelformset_factory
from django.db import transaction

from ralph_assets.models import Asset, OfficeInfo

from ralph_assets.views.base import AssetsBase, get_return_link
from ralph_assets.views.search import AssetSearch
from ralph_assets.models_history import AssetHistoryChange
from ralph_assets.models_assets import AssetType

MAX_PAGE_SIZE = 65535
HISTORY_PAGE_SIZE = 25

MAX_BULK_EDIT_SIZE = 40

logger = logging.getLogger(__name__)


def _move_data(src, dst, fields):
    for field in fields:
        if field in src:
            value = src.pop(field)
            dst[field] = value
    return src, dst


@transaction.commit_on_success
def _update_office_info(user, asset, office_info_data):
    if not asset.office_info:
        office_info = OfficeInfo()
    else:
        office_info = asset.office_info
    if 'attachment' in office_info_data:
        if office_info_data['attachment'] is None:
            del office_info_data['attachment']
        elif office_info_data['attachment'] is False:
            office_info_data['attachment'] = None
    office_info.__dict__.update(**office_info_data)
    office_info.save(user=user)
    asset.office_info = office_info
    asset.save(user=user)
    return asset


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


class BulkEdit(AssetSearch):
    template_name = 'assets/bulk_edit.html'

    def dispatch(self, request, mode=None, *args, **kwargs):
        self.mode = mode
        self.form_bulk = self.form_dispatcher('BulkEditAsset')
        return super(BulkEdit, self).dispatch(request, mode, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(BulkEdit, self).get_context_data(**kwargs)
        ret.update({
            'formset': self.asset_formset,
            'mode': self.mode,
        })
        return ret

    def get_items_ids(self, *args, **kwargs):
        items_ids = self.request.GET.getlist('select')
        try:
            int_ids = map(int, items_ids)
        except ValueError:
            int_ids = []
        return int_ids

    def get(self, *args, **kwargs):
        if self.request.GET.get('from_query'):
            query = super(
                BulkEdit, self,
            ).handle_search_data(*args, **kwargs)
        else:
            query = Q(pk__in=self.get_items_ids())
        assets_count = self.asset_objects.filter(query).count()
        if not (0 < assets_count <= MAX_BULK_EDIT_SIZE):
            if assets_count > MAX_BULK_EDIT_SIZE:
                messages.warning(
                    self.request,
                    _("You can edit max {} items".format(MAX_BULK_EDIT_SIZE)),
                )
            elif not assets_count:
                messages.warning(self.request, _("Nothing to edit."))
            return HttpResponseRedirect(get_return_link(self.mode))
        AssetFormSet = modelformset_factory(
            Asset,
            form=self.form_bulk,
            extra=0,
        )
        assets = self.asset_objects.filter(query)
        self.asset_formset = AssetFormSet(queryset=assets)
        for idx, asset in enumerate(assets):
            if asset.office_info:
                for field in ['purpose']:
                    if field not in self.asset_formset.forms[idx].fields:
                        continue
                    self.asset_formset.forms[idx].fields[field].initial = (
                        getattr(asset.office_info, field, None)
                    )
        return super(BulkEdit, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        AssetFormSet = modelformset_factory(
            Asset,
            form=self.form_bulk,
            extra=0,
        )
        self.asset_formset = AssetFormSet(self.request.POST)
        if self.asset_formset.is_valid():
            with transaction.commit_on_success():
                instances = self.asset_formset.save(commit=False)
                for idx, instance in enumerate(instances):
                    instance.modified_by = self.request.user.get_profile()
                    instance.save(user=self.request.user)
                    new_src, office_info_data = _move_data(
                        self.asset_formset.forms[idx].cleaned_data,
                        {}, ['purpose']
                    )
                    self.asset_formset.forms[idx].cleaned_data = new_src
                    instance = _update_office_info(
                        self.request.user, instance,
                        office_info_data,
                    )
            messages.success(self.request, _("Changes saved."))
            return HttpResponseRedirect(self.request.get_full_path())
        form_error = self.asset_formset.get_form_error()
        if form_error:
            messages.error(
                self.request,
                _(("Please correct errors and check both"
                  "\"serial numbers\" and \"barcodes\" for duplicates"))
            )
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(BulkEdit, self).get(*args, **kwargs)
