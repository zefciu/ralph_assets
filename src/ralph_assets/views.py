# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import logging
import re
import uuid

from collections import Counter
from bob.data_table import DataTableColumn, DataTableMixin
from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.fields import DecimalField
from django.db.models.fields.related import RelatedField
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.forms.models import modelformset_factory, formset_factory
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from inkpy.api import generate_pdf
from rq import get_current_job
from lck.django.common.models import Named

from ralph_assets import forms as assets_forms
from ralph_assets.forms import (
    AttachmentForm,
    AddDeviceForm,
    AddPartForm,
    BasePartForm,
    SplitDevice,
    DeviceForm,
    EditPartForm,
    MoveAssetPartForm,
    OfficeForm,
    BackOfficeSearchAssetForm,
    DataCenterSearchAssetForm,
)
from ralph_assets.forms_import import ColumnChoiceField, get_model_by_name
from ralph_assets.forms_sam import LicenceForm
from ralph_assets.models import (
    Asset,
    AssetModel,
    AssetCategory,
    DeviceInfo,
    Licence,
    OfficeInfo,
    PartInfo,
    ReportOdtSource,
    SoftwareCategory,
)
from ralph_assets.models_assets import (
    Attachment,
    AssetType,
    MODE2ASSET_TYPE,
    CreatableFromStr,
)
from ralph_assets.models_history import AssetHistoryChange
from ralph.business.models import Venture
from ralph.ui.views.common import Base
from ralph.util.api_assets import get_device_components
from ralph.util.reports import Report, set_progress

SAVE_PRIORITY = 200
HISTORY_PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535

QUOTATION_MARKS = re.compile(r"^\".+\"$")

logger = logging.getLogger(__name__)


def _move_data(src, dst, fields):
    for field in fields:
        if field in src:
            value = src.pop(field)
            dst[field] = value
    return src, dst


class AssetsBase(Base):
    template_name = "assets/base.html"

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetsBase, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
            'mainmenu_items': self.get_mainmenu_items(),
            'section': 'assets',
            'sidebar_selected': self.sidebar_selected,
            'section': self.mainmenu_selected,
            'mode': self.mode,
        })

        return ret

    def get_mainmenu_items(self):
        mainmenu = [
            MenuItem(
                label='Data center',
                name='dc',
                fugue_icon='fugue-building',
                href='/assets/dc',
            ),
            MenuItem(
                label='BackOffice',
                fugue_icon='fugue-printer',
                name='back_office',
                href='/assets/back_office',
            ),
        ]
        if 'ralph_pricing' in settings.INSTALLED_APPS:
            mainmenu.append(
                MenuItem(
                    label='Ralph Pricing',
                    fugue_icon='fugue-money-coin',
                    name='back_office',
                    href='/pricing/all-ventures/',
                ),
            )
        return mainmenu

    def get_sidebar_items(self):
        if self.mode == 'back_office':
            sidebar_caption = _('Back office actions')
            self.mainmenu_selected = 'back office'
        else:
            sidebar_caption = _('Data center actions')
            self.mainmenu_selected = 'dc'
        items = (
            ('add_device', _('Add device'), 'fugue-block--plus'),
            ('add_part', _('Add part'), 'fugue-block--plus'),
            ('asset_search', _('Search'), 'fugue-magnifier'),
            ('licence_list', _('Licence list'), 'fugue-cheque-sign'),
            ('add_licence', _('Add Licence'), 'fugue-cheque--plus'),
            ('xls_upload', _('XLS upload'), 'fugue-cheque--plus'),
        )
        sidebar_menu = (
            [MenuHeader(sidebar_caption)] +
            [MenuItem(
                label=label,
                fugue_icon=icon,
                href=reverse(view, kwargs={
                    'mode': (self.mode or 'dc')
                })
            ) for view, label, icon in items]
        )
        sidebar_menu += [
            MenuItem(
                label='Admin',
                fugue_icon='fugue-toolbox',
                href='/admin/ralph_assets',
            )
        ]
        return sidebar_menu

    def set_mode(self, mode):
        self.mode = mode

    def dispatch(self, request, mode=None, *args, **kwargs):
        self.request = request
        self.set_mode(mode)
        return super(AssetsBase, self).dispatch(request, *args, **kwargs)

    def write_office_info2asset_form(self):
        """
        Writes fields from office_info form to asset form.
        """
        if self.asset.type in AssetType.BO.choices:
            self.office_info_form = OfficeForm(instance=self.asset.office_info)
            fields = ['imei', 'purpose']
            for field in fields:
                if not field in self.asset_form.fields:
                    continue
                self.asset_form.fields[field].initial = (
                    getattr(self.asset.office_info, field, '')
                )

    def form_dispatcher(self, class_name):
        """
        Returns form class depending on view mode ('backoffice' or
        'datacenter') and passed *class_name* arg.

        :param class_name: base class name common for both views BO, DC
        :returns class: form class from *ralph_assets.forms* module
        :rtype class:
        """
        mode_name = (
            'BackOffice' if self.mode == 'back_office' else 'DataCenter'
        )
        form_class_name = "{}{}Form".format(mode_name, class_name)
        try:
            form_class = getattr(assets_forms, form_class_name)
        except AttributeError:
            raise Exception("No form class named: {}".format(form_class_name))
        return form_class


class DataTableColumnAssets(DataTableColumn):
    """
    A container object for all the information about a columns header

    :param foreign_field_name - set if field comes from foreign key
    """

    def __init__(self, header_name, foreign_field_name=None, **kwargs):
        super(DataTableColumnAssets, self).__init__(header_name, **kwargs)
        self.foreign_field_name = foreign_field_name


class _AssetSearch(AssetsBase, DataTableMixin):
    """
        The main-screen search form for all type of assets.
        (version without async reports)
    """
    rows_per_page = 15
    csv_file_name = 'ralph.csv'
    sort_variable_name = 'sort'
    export_variable_name = 'export'
    _ = DataTableColumnAssets
    sidebar_selected = 'search'
    template_name = 'assets/search_asset.html'
    columns = [
        _('Dropdown', selectable=True, bob_tag=True),
        _('Type', bob_tag=True),
        _('SN', field='sn', sort_expression='sn', bob_tag=True, export=True),
        _('Barcode', field='barcode', sort_expression='barcode', bob_tag=True,
          export=True),
        _('Invoice date', field='invoice_date', sort_expression='model',
          bob_tag=True, export=True),
        _('Model', field='model', sort_expression='model', bob_tag=True,
          export=True),
        _('Invoice no.', field='invoice_no', sort_expression='invoice_no',
          bob_tag=True, export=True),
        _('Order no.', field='order_no', sort_expression='order_no',
          bob_tag=True, export=True),
        _('Status', field='status', sort_expression='status',
          bob_tag=True, export=True),
        _('Warehouse', field='warehouse', sort_expression='warehouse',
          bob_tag=True, export=True),
        _('Venture', field='venture', sort_expression='venture',
          bob_tag=True, export=True),
        _('Department', field='department', foreign_field_name='venture',
          export=True),
        _('Price', field='price', sort_expression='price',
          bob_tag=True, export=True),
        _('Discovered', bob_tag=True, field='is_discovered', export=True,
            foreign_field_name='is_discovered'),
        _('Actions', bob_tag=True),
        _('Barcode salvaged', field='barcode_salvaged',
          foreign_field_name='part_info', export=True),
        _('Source device', field='source_device',
          foreign_field_name='part_info', export=True),
        _('Device', field='device',
          foreign_field_name='part_info', export=True),
        _('Provider', field='provider', export=True),
        _('Remarks', field='remarks', export=True),
        _('Source', field='source', export=True),
        _('Support peroid', field='support_peroid', export=True),
        _('Support type', field='support_type', export=True),
        _('Support void_reporting', field='support_void_reporting',
          export=True),
        _('Inventory number', field='niw', foreign_field_name='', export=True),
        _(
            'Ralph ID',
            field='device_info',
            foreign_field_name='ralph_device_id',
            export=True
        ),
        _('Type', field='type', export=True),
        _(
            'Deprecation rate',
            field='deprecation_rate',
            foreign_field_name='', export=True,
        ),
    ]

    def set_mode(self, mode):
        self.header = 'Search {} Assets'.format(
            {
                'dc': 'DC',
                'back_office': 'BO',
            }[mode]
        )
        if mode == 'dc':
            self.objects = Asset.objects_dc
            self.admin_objects = Asset.admin_objects_dc
            search_form = DataCenterSearchAssetForm
        elif mode == 'back_office':
            self.objects = Asset.objects_bo
            self.admin_objects = Asset.admin_objects_bo
            search_form = BackOfficeSearchAssetForm
        self.form = search_form(self.request.GET, mode=mode)
        super(_AssetSearch, self).set_mode(mode)

    def handle_search_data(self, get_csv=False):
        search_fields = [
            'id',
            'niw',
            'category',
            'invoice_no',
            'model',
            'order_no',
            'part_info',
            'provider',
            'sn',
            'status',
            'deleted',
            'manufacturer',
            'barcode',
            'device_info',
            'source',
            'deprecation_rate',
            'unlinked',
            'ralph_device_id',
            'task_url',
            'imei',
            'guardian',
            'user',
            'purpose',
        ]
        # handle simple 'equals' search fields at once.
        all_q = Q()
        for field in search_fields:
            field_value = self.request.GET.get(field)
            if field_value:
                exact = False
                # if search term is enclosed in "", we want exact matches
                if isinstance(field_value, basestring) and \
                        QUOTATION_MARKS.search(field_value):
                    exact = True
                    field_value = field_value[1:-1]
                if field == 'part_info':
                    if field_value == 'device':
                        all_q &= Q(part_info__isnull=True)
                    elif field_value == 'part':
                        all_q &= Q(part_info__gte=0)
                elif field == 'model':
                    if exact:
                        all_q &= Q(model__name=field_value)
                    else:
                        all_q &= Q(model__name__icontains=field_value)
                elif field == 'category':
                    part = self.get_search_category_part(field_value)
                    if part:
                        all_q &= part
                elif field == 'deleted':
                    if field_value.lower() == 'on':
                        all_q &= Q(deleted__in=(True, False))
                elif field == 'manufacturer':
                    if exact:
                        all_q &= Q(model__manufacturer__name=field_value)
                    else:
                        all_q &= Q(
                            model__manufacturer__name__icontains=field_value
                        )
                elif field == 'barcode':
                    if exact:
                        all_q &= Q(barcode=field_value)
                    else:
                        all_q &= Q(barcode__contains=field_value)
                elif field == 'sn':
                    if exact:
                        all_q &= Q(sn=field_value)
                    else:
                        all_q &= Q(sn__icontains=field_value)
                elif field == 'niw':
                    if exact:
                        all_q &= Q(niw=field_value)
                    else:
                        all_q &= Q(niw__icontains=field_value)
                elif field == 'provider':
                    if exact:
                        all_q &= Q(provider=field_value)
                    else:
                        all_q &= Q(provider__icontains=field_value)
                elif field == 'order_no':
                    if exact:
                        all_q &= Q(order_no=field_value)
                    else:
                        all_q &= Q(order_no__icontains=field_value)
                elif field == 'invoice_no':
                    if exact:
                        all_q &= Q(invoice_no=field_value)
                    else:
                        all_q &= Q(invoice_no__icontains=field_value)
                elif field == 'user':
                    all_q &= Q(user__id=field_value)
                elif field == 'guardian':
                    all_q &= Q(guardian__id=field_value)
                elif field == 'deprecation_rate':
                    deprecation_rate_query_map = {
                        'null': Q(deprecation_rate__isnull=True),
                        'deprecated': Q(deprecation_rate=0),
                        '6': Q(deprecation_rate__gt=0,
                               deprecation_rate__lte=6),
                        '12': Q(deprecation_rate__gt=6,
                                deprecation_rate__lte=12),
                        '24': Q(deprecation_rate__gt=12,
                                deprecation_rate__lte=24),
                        '48': Q(deprecation_rate__gt=24,
                                deprecation_rate__lte=48),
                        '48<': Q(deprecation_rate__gt=48),
                    }
                    all_q &= deprecation_rate_query_map[field_value]
                elif field == 'unlinked' and field_value.lower() == 'on':
                        all_q &= ~Q(device_info=None)
                        all_q &= Q(device_info__ralph_device_id=None)
                elif field == 'ralph_device_id':
                    if exact:
                        all_q &= Q(device_info__ralph_device_id=field_value)
                    else:
                        all_q &= Q(
                            device_info__ralph_device_id__icontains=field_value
                        )
                elif field == 'task_url':
                    if exact:
                        all_q &= Q(task_url=field_value)
                    else:
                        all_q &= Q(task_url__icontains=field_value)
                elif field == 'id':
                        all_q &= Q(
                            id__in=[int(id) for id in field_value.split(",")],
                        )
                elif field == 'imei':
                    if exact:
                        all_q &= Q(office_info__imei=field_value)
                    else:
                        all_q &= Q(office_info__imei__icontains=field_value)
                elif field == 'purpose':
                    all_q &= Q(office_info__purpose=field_value)
                else:
                    q = Q(**{field: field_value})
                    all_q = all_q & q

        # now fields within ranges.
        search_date_fields = [
            'invoice_date', 'request_date', 'delivery_date',
            'production_use_date', 'provider_order_date',
        ]
        for date in search_date_fields:
            start = self.request.GET.get(date + '_from')
            end = self.request.GET.get(date + '_to')
            if start:
                all_q &= Q(**{date + '__gte': start})
            if end:
                all_q &= Q(**{date + '__lte': end})
        if get_csv:
            return self.get_csv_data(self.get_all_items(all_q))
        else:
            self.data_table_query(self.get_all_items(all_q))

    def get_search_category_part(self, field_value):
        try:
            category_id = field_value
        except ValueError:
            pass
        else:
            category = AssetCategory.objects.get(slug=category_id)
            children = [x.slug for x in category.get_children()]
            categories = [category_id, ] + children
            return Q(category_id__in=categories)

    def get_csv_header(self):
        header = super(_AssetSearch, self).get_csv_header()
        return ['type'] + header

    def get_csv_rows(self, queryset, type, model):
        data = [self.get_csv_header()]
        total = queryset.count()
        processed = 0
        job = get_current_job()
        for asset in queryset:
            row = ['part', ] if asset.part_info else ['device', ]
            for item in self.columns:
                field = item.field
                if field:
                    nested_field_name = item.foreign_field_name
                    if nested_field_name == type:
                        cell = self.get_cell(
                            getattr(asset, type), field, model
                        )
                    elif nested_field_name == 'part_info':
                        cell = self.get_cell(asset.part_info, field, PartInfo)
                    elif nested_field_name == 'venture':
                        cell = self.get_cell(asset.venture, field, Venture)
                    elif nested_field_name == 'is_discovered':
                        cell = unicode(asset.is_discovered)
                    else:
                        cell = self.get_cell(asset, field, Asset)
                    row.append(unicode(cell))
            data.append(row)
            processed += 1
            set_progress(job, processed / total)
        set_progress(job, 1)
        return data

    def get_all_items(self, query):
        include_deleted = self.request.GET.get('deleted')
        if include_deleted and include_deleted.lower() == 'on':
            return self.admin_objects.filter(query)
        return self.objects.filter(query)

    def get_context_data(self, *args, **kwargs):
        ret = super(_AssetSearch, self).get_context_data(*args, **kwargs)
        ret.update(
            super(_AssetSearch, self).get_context_data_paginator(
                *args,
                **kwargs
            )
        )
        ret.update({
            'form': self.form,
            'header': self.header,
            'sort': self.sort,
            'columns': self.columns,
            'sort_variable_name': self.sort_variable_name,
            'export_variable_name': self.export_variable_name,
            'csv_url': self.request.path_info + '/csv',
            'asset_reports_enable': settings.ASSETS_REPORTS['ENABLE'],
        })
        return ret

    def get(self, *args, **kwargs):
        self.handle_search_data()
        if self.export_requested():
            return self.response
        return super(_AssetSearch, self).get(*args, **kwargs)

    def is_async(self, request, *args, **kwargs):
        self.export = request.GET.get('export')
        return self.export == 'csv'

    def get_result(self, request, *args, **kwargs):
        self.set_mode(kwargs['mode'])
        return self.handle_search_data(get_csv=True)

    def get_response(self, request, result):
        return self.make_csv_response(result)

    def get_csv_data(self, queryset):
        return self.get_csv_rows(
            queryset, type='office_info', model=OfficeInfo
        )

    def get_columns_nested(self, mode):
        _ = DataTableColumnAssets
        if mode == 'back_office':
            return [
                _(
                    'Date of last inventory',
                    field='date_of_last_inventory',
                    foreign_field_name='office_info',
                    export=True,
                ),
                _(
                    'Last logged user',
                    field='last_logged_user',
                    foreign_field_name='office_info',
                    export=True,
                ),
                _(
                    'License key',
                    field='license_key',
                    foreign_field_name='office_info',
                    export=True,
                ),
                _(
                    'License type',
                    field='license_type',
                    foreign_field_name='office_info',
                    export=True,
                ),
                _(
                    'Unit price',
                    field='unit_price',
                    foreign_field_name='office_info',
                    export=True,
                ),
                _(
                    'Version',
                    field='version',
                    foreign_field_name='office_info',
                    export=True,
                ),
            ]
        elif mode == 'dc':
            return [
                _(
                    'asset id',
                    field='id',
                    export=True,
                ),
                _(
                    'Ralph device id',
                    field='ralph_device_id',
                    foreign_field_name='device_info',
                    export=True,
                ), _(
                    'Rack',
                    field='rack',
                    foreign_field_name='device_info',
                    export=True,
                ),
                _(
                    'U level',
                    field='u_level',
                    foreign_field_name='device_info',
                    export=True,
                ),
                _(
                    'U height',
                    field='u_height',
                    foreign_field_name='device_info',
                    export=True,
                ),
                _(
                    'modified',
                    field='modified',
                    export=True,
                ),

            ]


class AssetSearch(Report, _AssetSearch):
    """The main-screen search form for all type of assets."""


def _get_return_link(mode):
    return "/assets/%s/" % mode


@transaction.commit_on_success
def _create_device(creator_profile, asset_data, device_info_data, sn, mode,
                   barcode=None, office_info_data=None):
    device_info = DeviceInfo()
    if mode == 'dc':
        device_info.ralph_device_id = device_info_data['ralph_device_id']
        device_info.u_level = device_info_data['u_level']
        device_info.u_height = device_info_data['u_height']
    device_info.save(user=creator_profile.user)
    asset = Asset(
        device_info=device_info,
        sn=sn.strip(),
        created_by=creator_profile,
        **asset_data
    )
    if barcode:
        asset.barcode = barcode
    if office_info_data:
        _update_office_info(creator_profile.user, asset, office_info_data)
    asset.save(user=creator_profile.user)
    return asset.id


class AddDevice(AssetsBase):
    template_name = 'assets/add_device.html'
    sidebar_selected = 'add device'

    def get_context_data(self, **kwargs):
        ret = super(AddDevice, self).get_context_data(**kwargs)
        ret.update({
            'asset_form': self.asset_form,
            'device_info_form': self.device_info_form,
            'form_id': 'add_device_asset_form',
            'edit_mode': False,
        })
        return ret

    def get(self, *args, **kwargs):
        mode = self.mode
        self.asset_form = AddDeviceForm(mode=mode)
        device_form_class = self.form_dispatcher('AddDevice')
        self.asset_form = device_form_class(mode=self.mode)
        self.device_info_form = DeviceForm(
            mode=mode,
            exclude='create_stock',
        )
        return super(AddDevice, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        mode = self.mode
        device_form_class = self.form_dispatcher('AddDevice')
        self.asset_form = device_form_class(self.request.POST, mode=self.mode)
        self.device_info_form = DeviceForm(
            self.request.POST,
            mode=mode,
            exclude='create_stock',
        )
        if self.asset_form.is_valid() and self.device_info_form.is_valid():
            creator_profile = self.request.user.get_profile()
            asset_data = {}
            for f_name, f_value in self.asset_form.cleaned_data.items():
                if f_name in ["barcode", "sn", "imei"]:
                    continue
                asset_data[f_name] = f_value
            serial_numbers = self.asset_form.cleaned_data['sn']
            barcodes = self.asset_form.cleaned_data['barcode']
            imeis = (
                self.asset_form.cleaned_data.pop('imei')
                if 'imei' in self.asset_form.cleaned_data else None
            )
            office_info_data = {}
            asset_data, office_info_data = _move_data(
                asset_data, office_info_data, ['purpose']
            )
            ids = []
            for sn, index in zip(serial_numbers, range(len(serial_numbers))):
                barcode = barcodes[index] if barcodes else None
                if imeis:
                    office_info_data['imei'] = imeis[index]
                ids.append(
                    _create_device(
                        creator_profile,
                        asset_data,
                        self.device_info_form.cleaned_data,
                        sn,
                        mode,
                        barcode,
                        office_info_data,
                    )
                )
            messages.success(self.request, _("Assets saved."))
            cat = self.request.path.split('/')[2]
            if len(ids) == 1:
                return HttpResponseRedirect(
                    '/assets/%s/edit/device/%s/' % (cat, ids[0])
                )
            else:
                return HttpResponseRedirect(
                    '/assets/%s/bulkedit/?select=%s' % (
                        cat, '&select='.join(["%s" % id for id in ids]))
                )
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddDevice, self).get(*args, **kwargs)


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


@transaction.commit_on_success
def _update_device_info(user, asset, device_info_data):
    asset.device_info.__dict__.update(
        **device_info_data
    )
    asset.device_info.save(user=user)
    return asset


@transaction.commit_on_success
def _update_part_info(user, asset, part_info_data):
    if not asset.part_info:
        part_info = PartInfo()
    else:
        part_info = asset.part_info
    part_info.device = part_info_data.get('device')
    part_info.source_device = part_info_data.get('source_device')
    part_info.barcode_salvaged = part_info_data.get('barcode_salvaged')
    part_info.save(user=user)
    asset.part_info = part_info
    asset.part_info.save(user=user)
    return asset


class EditDevice(AssetsBase):
    template_name = 'assets/edit_device.html'
    sidebar_selected = 'edit device'

    def initialize_vars(self):
        self.parts = []
        self.office_info_form = None
        self.asset = None

    def get_context_data(self, **kwargs):
        ret = super(EditDevice, self).get_context_data(**kwargs)
        status_history = AssetHistoryChange.objects.all().filter(
            asset=kwargs.get('asset_id'), field_name__exact='status'
        ).order_by('-date')
        ret.update({
            'asset_form': self.asset_form,
            'device_info_form': self.device_info_form,
            'office_info_form': self.office_info_form,
            'part_form': MoveAssetPartForm(),
            'form_id': 'edit_device_asset_form',
            'edit_mode': True,
            'status_history': status_history,
            'parts': self.parts,
            'asset': self.asset,
            'history_link': self.get_history_link(),
        })
        return ret

    def get(self, *args, **kwargs):
        self.initialize_vars()
        self.asset = get_object_or_404(
            Asset.admin_objects,
            id=kwargs.get('asset_id')
        )
        if not self.asset.device_info:  # it isn't device asset
            raise Http404()
        device_form_class = self.form_dispatcher('EditDevice')
        self.asset_form = device_form_class(
            instance=self.asset, mode=self.mode
        )
        self.write_office_info2asset_form()
        self.device_info_form = DeviceForm(
            instance=self.asset.device_info,
            mode=self.mode,
        )
        self.parts = Asset.objects.filter(part_info__device=self.asset)
        return super(EditDevice, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.initialize_vars()
        post_data = self.request.POST
        self.asset = get_object_or_404(
            Asset.admin_objects,
            id=kwargs.get('asset_id')
        )
        device_form_class = self.form_dispatcher('EditDevice')
        self.asset_form = device_form_class(
            post_data,
            instance=self.asset,
            mode=self.mode,
        )
        self.device_info_form = DeviceForm(
            post_data,
            mode=self.mode,
            instance=self.asset.device_info,
        )
        self.part_form = MoveAssetPartForm(post_data)
        if 'move_parts' in post_data.keys():
            destination_asset = post_data.get('new_asset')
            if not destination_asset or not Asset.objects.filter(
                id=destination_asset,
            ):
                messages.error(
                    self.request,
                    _("Source device asset does not exist"),
                )
            elif kwargs.get('asset_id') == destination_asset:
                messages.error(
                    self.request,
                    _("You can't move parts to the same device"),
                )
            else:
                for part_id in post_data.get('part_ids'):
                    info_part = PartInfo.objects.get(asset=part_id)
                    info_part.device_id = destination_asset
                    info_part.save()
                messages.success(self.request, _("Selected parts was moved."))
        elif 'asset' in post_data.keys():
            if self.asset.type in AssetType.BO.choices:
                self.office_info_form = OfficeForm(
                    post_data, self.request.FILES,
                )
            if all((
                self.asset_form.is_valid(),
                self.device_info_form.is_valid(),
                self.asset.type not in AssetType.BO.choices or
                self.office_info_form.is_valid()
            )):
                modifier_profile = self.request.user.get_profile()
                self.asset = _update_asset(
                    modifier_profile, self.asset, self.asset_form.cleaned_data
                )

                if self.asset.type in AssetType.BO.choices:
                    new_src, new_dst = _move_data(
                        self.asset_form.cleaned_data,
                        self.office_info_form.cleaned_data,
                        ['imei', 'purpose'],
                    )
                    self.asset_form.cleaned_data = new_src
                    self.office_info_form.cleaned_data = new_dst
                    self.asset = _update_office_info(
                        modifier_profile.user, self.asset,
                        self.office_info_form.cleaned_data
                    )
                self.asset = _update_device_info(
                    modifier_profile.user, self.asset,
                    self.device_info_form.cleaned_data
                )
                if self.device_info_form.cleaned_data.get('create_stock'):
                    self.asset.create_stock_device()
                self.asset.save(user=self.request.user)
                messages.success(self.request, _("Assets edited."))
                cat = self.request.path.split('/')[2]
                return HttpResponseRedirect(
                    '/assets/%s/edit/device/%s/' % (cat, self.asset.id)
                )
            else:
                messages.error(self.request, _("Please correct the errors."))
                messages.error(
                    self.request, self.asset_form.non_field_errors(),
                )
        return super(EditDevice, self).get(*args, **kwargs)

    def get_history_link(self):
        asset_id = self.asset.id
        url = reverse('device_history', kwargs={
            'asset_id': asset_id,
            'mode': self.mode,
        })
        return url


class EditPart(AssetsBase):
    template_name = 'assets/edit_part.html'
    sidebar_selected = None

    def initialize_vars(self):
        self.office_info_form = None

    def get_context_data(self, **kwargs):
        ret = super(EditPart, self).get_context_data(**kwargs)
        status_history = AssetHistoryChange.objects.all().filter(
            asset=kwargs.get('asset_id'), field_name__exact='status'
        ).order_by('-date')
        ret.update({
            'asset_form': self.asset_form,
            'office_info_form': self.office_info_form,
            'part_info_form': self.part_info_form,
            'form_id': 'edit_part_form',
            'edit_mode': True,
            'status_history': status_history,
            'history_link': self.get_history_link(),
            'parent_link': self.get_parent_link(),
        })
        return ret

    def get(self, *args, **kwargs):
        self.initialize_vars()
        self.asset = get_object_or_404(
            Asset.admin_objects,
            id=kwargs.get('asset_id')
        )
        if self.asset.device_info:  # it isn't part asset
            raise Http404()
        self.asset_form = EditPartForm(instance=self.asset, mode=self.mode)
        self.write_office_info2asset_form()
        self.part_info_form = BasePartForm(
            instance=self.asset.part_info, mode=self.mode,
        )
        return super(EditPart, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.asset = get_object_or_404(
            Asset.admin_objects,
            id=kwargs.get('asset_id')
        )
        mode = self.mode
        self.asset_form = EditPartForm(
            self.request.POST,
            instance=self.asset,
            mode=mode
        )
        self.office_info_form = OfficeForm(
            self.request.POST, self.request.FILES)
        self.part_info_form = BasePartForm(self.request.POST, mode=mode)
        if all((
            self.asset_form.is_valid(),
            self.office_info_form.is_valid(),
            self.part_info_form.is_valid()
        )):
            modifier_profile = self.request.user.get_profile()
            self.asset = _update_asset(
                modifier_profile, self.asset,
                self.asset_form.cleaned_data
            )
            new_src, new_dst = _move_data(
                self.asset_form.cleaned_data,
                self.office_info_form.cleaned_data,
                ['imei'],
            )
            self.asset_form.cleaned_data = new_src
            self.office_info_form.cleaned_data = new_dst
            self.asset = _update_office_info(
                modifier_profile.user, self.asset,
                self.office_info_form.cleaned_data
            )
            self.asset = _update_part_info(
                modifier_profile.user, self.asset,
                self.part_info_form.cleaned_data
            )
            self.asset.save(user=self.request.user)
            messages.success(self.request, _("Part of asset was edited."))
            cat = self.request.path.split('/')[2]
            return HttpResponseRedirect(
                '/assets/%s/edit/part/%s/' % (cat, self.asset.id)
            )
        else:
            messages.error(self.request, _("Please correct the errors."))
            messages.error(self.request, self.asset_form.non_field_errors())
        return super(EditPart, self).get(*args, **kwargs)

    def get_parent_link(self):
        asset = self.asset.part_info.source_device
        if asset:
            return reverse('dc_device_edit', kwargs={
                'asset_id': asset.id,
                'mode': self.mode,
            })

    def get_history_link(self):
        return reverse('part_history', kwargs={
            'asset_id': self.asset.id,
            'mode': self.mode,
        })


class BulkEdit(AssetsBase, Base):
    template_name = 'assets/bulk_edit.html'
    sidebar_selected = None

    def get_context_data(self, **kwargs):
        ret = super(BulkEdit, self).get_context_data(**kwargs)
        ret.update({
            'formset': self.asset_formset,
            'mode': self.mode,
        })
        return ret

    def get(self, *args, **kwargs):
        assets_count = Asset.objects.filter(
            pk__in=self.request.GET.getlist('select')).exists()
        if not assets_count:
            messages.warning(self.request, _("Nothing to edit."))
            return HttpResponseRedirect(_get_return_link(self.mode))
        bulk_form_class = self.form_dispatcher('BulkEditAsset')
        AssetFormSet = modelformset_factory(
            Asset,
            form=bulk_form_class,
            extra=0,
        )
        assets = Asset.objects.filter(
            pk__in=self.request.GET.getlist('select')
        )
        self.asset_formset = AssetFormSet(queryset=assets)
        for idx, asset in enumerate(assets):
            if asset.office_info:
                for field in ['purpose']:
                    if not field in self.asset_formset.forms[idx].fields:
                        continue
                    self.asset_formset.forms[idx].fields[field].initial = (
                        getattr(asset.office_info, field, None)
                    )
        return super(BulkEdit, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        bulk_form_class = self.form_dispatcher('BulkEditAsset')
        AssetFormSet = modelformset_factory(
            Asset,
            form=bulk_form_class,
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
            return HttpResponseRedirect(_get_return_link(self.mode))
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


@transaction.commit_on_success
def _create_part(creator_profile, asset_data, part_info_data, sn):
    part_info = PartInfo(**part_info_data)
    part_info.save(user=creator_profile.user)
    asset = Asset(
        part_info=part_info,
        sn=sn.strip(),
        created_by=creator_profile,
        **asset_data
    )
    asset.save(user=creator_profile.user)
    return asset.id


class AddPart(AssetsBase):
    template_name = 'assets/add_part.html'
    sidebar_selected = 'add part'

    def get_context_data(self, **kwargs):
        ret = super(AddPart, self).get_context_data(**kwargs)
        ret.update({
            'asset_form': self.asset_form,
            'part_info_form': self.part_info_form,
            'form_id': 'add_part_form',
            'edit_mode': False,
        })
        return ret

    def initialize_vars(self):
        self.device_id = None

    def get(self, *args, **kwargs):
        self.initialize_vars()
        mode = self.mode
        self.asset_form = AddPartForm(mode=mode)
        self.device_id = self.request.GET.get('device')
        part_form_initial = {}
        if self.device_id:
            part_form_initial['device'] = self.device_id
        self.part_info_form = BasePartForm(
            initial=part_form_initial, mode=mode)
        return super(AddPart, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.initialize_vars()
        mode = self.mode
        self.asset_form = AddPartForm(self.request.POST, mode=mode)
        self.part_info_form = BasePartForm(self.request.POST, mode=mode)
        if self.asset_form.is_valid() and self.part_info_form.is_valid():
            creator_profile = self.request.user.get_profile()
            asset_data = self.asset_form.cleaned_data
            asset_data['barcode'] = None
            serial_numbers = self.asset_form.cleaned_data['sn']
            del asset_data['sn']
            if 'imei' in asset_data:
                del asset_data['imei']
            ids = []
            for sn in serial_numbers:
                ids.append(
                    _create_part(
                        creator_profile, asset_data,
                        self.part_info_form.cleaned_data, sn
                    )
                )
            messages.success(self.request, _("Assets saved."))
            cat = self.request.path.split('/')[2]
            if len(ids) == 1:
                return HttpResponseRedirect(
                    '/assets/%s/edit/part/%s/' % (cat, ids[0])
                )
            else:
                return HttpResponseRedirect(
                    '/assets/%s/bulkedit/?select=%s' % (
                        cat, '&select='.join(["%s" % id for id in ids]))
                )
            return HttpResponseRedirect(_get_return_link(self.mode))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddPart, self).get(*args, **kwargs)


class HistoryAsset(AssetsBase):
    template_name = 'assets/history_asset.html'
    sidebar_selected = None

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
        ret.update({
            'history': history,
            'history_page': history_page,
            'status': status,
            'query_variable_name': query_variable_name,
            'asset': asset,
        })
        return ret


class SplitDeviceView(AssetsBase):
    template_name = 'assets/split_edit.html'
    sidebar_selected = ''

    def get_context_data(self, **kwargs):
        ret = super(SplitDeviceView, self).get_context_data(**kwargs)
        ret.update({
            'formset': self.asset_formset,
            'device': {
                'model': self.asset.model,
                'sn': self.asset.sn,
                'price': self.asset.price,
                'id': self.asset.id,
            },
        })
        return ret

    def get(self, *args, **kwargs):
        self.asset_id = self.kwargs.get('asset_id')
        self.asset = get_object_or_404(Asset, id=self.asset_id)
        if self.asset.has_parts():
            messages.error(self.request, _("This asset was splited."))
            return HttpResponseRedirect(
                reverse('device_edit', args=[self.asset.id, ])
            )
        if self.asset.device_info.ralph_device_id:
            initial = self.get_proposed_components()
        else:
            initial = []
            messages.error(
                self.request,
                _(
                    'Asset not linked with ralph device, proposed components '
                    'not available'
                ),
            )
        extra = 0 if initial else 1
        AssetFormSet = formset_factory(form=SplitDevice, extra=extra)
        self.asset_formset = AssetFormSet(initial=initial)
        return super(SplitDeviceView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.asset_id = self.kwargs.get('asset_id')
        self.asset = Asset.objects.get(id=self.asset_id)
        AssetFormSet = formset_factory(
            form=SplitDevice,
            extra=0,
        )
        self.asset_formset = AssetFormSet(self.request.POST)
        if self.asset_formset.is_valid():
            with transaction.commit_on_success():
                for instance in self.asset_formset.forms:
                    form = instance.save(commit=False)
                    model_name = instance['model_user'].value()
                    form.model = self.create_asset_model(model_name)
                    form.type = AssetType.data_center
                    form.part_info = self.create_part_info()
                    form.modified_by = self.request.user.get_profile()
                    form.save(user=self.request.user)
            messages.success(self.request, _("Changes saved."))
            return HttpResponseRedirect(self.request.get_full_path())
        self.valid_duplicates('sn')
        self.valid_duplicates('barcode')
        self.valid_total_price()
        messages.error(self.request, _("Please correct the errors."))
        return super(SplitDeviceView, self).get(*args, **kwargs)

    def valid_total_price(self):
        total_price = 0
        for instance in self.asset_formset.forms:
            total_price += float(instance['price'].value() or 0)
        valid_price = True if total_price == self.asset.price else False
        if not valid_price:
            messages.error(
                self.request,
                _(
                    "Total parts price must be equal to the asset price. "
                    "Total parts price (%s) != Asset "
                    "price (%s)" % (total_price, self.asset.price)
                )
            )
            return True

    def valid_duplicates(self, name):
        def get_duplicates(list):
            cnt = Counter(list)
            return [key for key in cnt.keys() if cnt[key] > 1]
        items = []
        for instance in self.asset_formset.forms:
            value = instance[name].value().strip()
            if value:
                items.append(value)
        duplicates_items = get_duplicates(items)
        for instance in self.asset_formset.forms:
            value = instance[name].value().strip()
            if value in duplicates_items:
                if name in instance.errors:
                    instance.errors[name].append(
                        'This %s is duplicated' % name
                    )
                else:
                    instance.errors[name] = ['This %s is duplicated' % name]
        if duplicates_items:
            messages.error(
                self.request,
                _("This %s is duplicated: (%s) " % (
                    name,
                    ', '.join(duplicates_items)
                )),
            )
            return True

    def create_asset_model(self, model_name):
        try:
            model = AssetModel.objects.get(name=model_name)
        except AssetModel.DoesNotExist:
            model = AssetModel()
            model.name = model_name
            model.save()
        return model

    def create_part_info(self):
        part_info = PartInfo()
        part_info.source_device = self.asset
        part_info.device = self.asset
        part_info.save(user=self.request.user)
        return part_info

    def get_proposed_components(self):
        try:
            components = list(get_device_components(
                ralph_device_id=self.asset.device_info.ralph_device_id
            ))
        except LookupError:
            components = []
        return components


class XlsUploadView(SessionWizardView, AssetsBase):
    """The wizard view for xls/csv upload."""
    template_name = 'assets/xls_upload_wizard.html'
    file_storage = FileSystemStorage(location=settings.FILE_UPLOAD_TEMP_DIR)
    sidebar_selected = None
    mainmenu_selected = 'dc'

    def get_form(self, step=None, data=None, files=None):
        form = super(XlsUploadView, self).get_form(step, data, files)
        if step == 'column_choice':
            names_per_sheet, update_per_sheet, add_per_sheet =\
                self.get_cleaned_data_for_step('upload')['file']
            self.storage.data['names_per_sheet'] = names_per_sheet
            self.storage.data['update_per_sheet'] = update_per_sheet
            self.storage.data['add_per_sheet'] = add_per_sheet
            for name_list in names_per_sheet.values():
                for name in name_list:
                    form.fields[name] = ColumnChoiceField(
                        model=self.get_cleaned_data_for_step(
                            'upload',
                        )['model'],
                        label=name,
                    )
        elif step == 'confirm':
            mappings = {}
            all_names = set(sum((
                list(name_list)
                for name_list in self.storage.data['names_per_sheet'].values()
            ), []))
            for k, v in self.get_cleaned_data_for_step(
                'column_choice'
            ).items():
                if k in all_names and v != '':
                    mappings[k] = v
            self.storage.data['mappings'] = mappings
        return form

    def get_context_data(self, form, **kwargs):
        data = super(XlsUploadView, self).get_context_data(form, **kwargs)
        if self.steps.current == 'confirm':
            mappings = self.storage.data['mappings']
            update_per_sheet = self.storage.data['update_per_sheet']
            add_per_sheet = self.storage.data['add_per_sheet']
            all_columns = list(mappings.values())
            data_dicts = {}
            for sheet_name, sheet_data in update_per_sheet.items():
                for asset_id, asset_data in sheet_data.items():
                    data_dicts.setdefault(asset_id, {})
                    for key, value in asset_data.items():
                        data_dicts[asset_id][mappings[key]] = value
            update_table = []
            for asset_id, asset_data in data_dicts.items():
                row = [asset_id]
                for column in all_columns:
                    row.append(asset_data.get(column, ''))
                update_table.append(row)
            add_table = []
            for sheet_name, sheet_data in add_per_sheet.items():
                for asset_data in sheet_data:
                    asset_data = dict(
                        (mappings[k], v)
                        for (k, v) in asset_data.items()
                        if k in mappings
                    )
                    row = []
                    for column in all_columns:
                        row.append(asset_data.get(column, ''))
                    add_table.append(row)
            data['all_columns'] = all_columns
            data['update_table'] = update_table
            data['add_table'] = add_table
        return data

    def _get_field_value(self, field_name, value):
        """Transform a pure string into the value to be put into the field."""
        if not value:
            return
        field, _, _, _ = self.Model._meta.get_field_by_name(
            field_name
        )
        if isinstance(field, DecimalField):
            if value.count(',') == 1 and '.' not in value:
                value = value.replace(',', '.')

        if (
            isinstance(value, basestring) and
            isinstance(field, RelatedField) and
            issubclass(field.rel.to, Named)
        ):
            try:
                value = field.rel.to.objects.get(name=value)
            except field.rel.to.DoesNotExist:
                if issubclass(field.rel.to, CreatableFromStr):
                    value = field.rel.to.create_from_string(
                        asset_type=MODE2ASSET_TYPE[self.mode],
                        s=value
                    )
                    value.save()
                else:
                    raise
        return value

    @transaction.commit_on_success
    def done(self, form_list):
        mappings = self.storage.data['mappings']
        update_per_sheet = self.storage.data['update_per_sheet']
        add_per_sheet = self.storage.data['add_per_sheet']
        failed_assets = []
        self.Model = get_model_by_name(
            self.get_cleaned_data_for_step('upload')['model']
        )
        for sheet_name, sheet_data in update_per_sheet.items():
            for asset_id, asset_data in sheet_data.items():
                try:
                    asset = self.Model.objects.get(pk=asset_id)
                except ObjectDoesNotExist:
                    failed_assets.append(asset_id)
                    continue
                for key, value in asset_data.items():
                    setattr(
                        asset, mappings[key],
                        self._get_field_value(mappings[key], value)
                    )
                asset.save()
        for sheet_name, sheet_data in add_per_sheet.items():
            for asset_data in sheet_data:
                kwargs = dict(
                    (
                        mappings[key],
                        self._get_field_value(mappings[key], value)
                    ) for key, value in asset_data.items()
                    if key in mappings
                )
                asset = self.Model(**kwargs)
                if isinstance(asset, Asset):
                    asset.type = MODE2ASSET_TYPE[self.mode]
                else:
                    asset.asset_type = MODE2ASSET_TYPE[self.mode]
                asset.save()
        ctx_data = self.get_context_data(None)
        ctx_data['failed_assets'] = failed_assets
        return render(
            self.request,
            'assets/xls_upload_wizard_done.html',
            ctx_data
        )


class LicenceFormView(AssetsBase):
    """Base view that displays licence form."""

    template_name = 'assets/add_licence.html'
    sidebar_selected = None

    def _get_form(self, data=None, **kwargs):
        self.form = LicenceForm(
            mode=self.mode, data=data, **kwargs
        )

    def get_context_data(self, **kwargs):
        ret = super(LicenceFormView, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_licence_form',
            'edit_mode': False,
            'caption': self.caption,
        })
        return ret

    def _save(self, request, *args, **kwargs):
        try:
            licence = self.form.save(commit=False)
            if licence.asset_type is None:
                licence.asset_type = MODE2ASSET_TYPE[self.mode]
            licence.save()
            return HttpResponseRedirect(licence.url)
        except ValueError:
            return super(LicenceFormView, self).get(request, *args, **kwargs)


class AddLicence(LicenceFormView):
    """Add a new licence"""

    caption = _('Add Licence')

    def get(self, request, *args, **kwargs):
        self._get_form()
        return super(AddLicence, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._get_form(request.POST)
        return self._save(request, *args, **kwargs)


class EditLicence(LicenceFormView):
    """Edit licence"""

    caption = _('Edit Licence')

    def get(self, request, licence_id, *args, **kwargs):
        licence = Licence.objects.get(pk=licence_id)
        self._get_form(instance=licence)
        return super(EditLicence, self).get(request, *args, **kwargs)

    def post(self, request, licence_id, *args, **kwargs):
        licence = Licence.objects.get(pk=licence_id)
        self._get_form(request.POST, instance=licence)
        return self._save(request, *args, **kwargs)


class LicenceList(AssetsBase):
    """The licence list."""

    template_name = "assets/licence_list.html"
    sidebar_selected = None

    def get_context_data(self, *args, **kwargs):
        data = super(LicenceList, self).get_context_data(
            *args, **kwargs
        )
        data['categories'] = SoftwareCategory.objects.annotate(
            used=Sum('licence__used')
        ).filter(asset_type=MODE2ASSET_TYPE[self.mode])
        return data


class InvoiceReport(AssetsBase):
    template_name = 'assets/invoice_report.html'
    sidebar_selected = None

    def show_unique_error_message(self, *args, **kwargs):
        non_unique = {}
        for name in ['invoice_no', 'invoice_date', 'provider']:
            assets = self.assets.values(name).distinct()
            if assets.count() != 1:
                if name == 'invoice_date':
                    data = ", ".join(
                        asset[name].strftime(
                            "%d-%m-%Y"
                        ) for asset in assets if asset[name]
                    )
                else:
                    data = ", ".join(
                        asset[name] for asset in assets if asset[name]
                    )
                non_unique[name] = data
        non_unique_items = " ".join(
            [
                "{}: {}".format(
                    key, value,
                ) for key, value in non_unique.iteritems() if value
            ]
        )
        messages.error(
            self.request,
            "{}: {}".format(
                _("Selected asset has different: "),
                non_unique_items,
            )
        )

    def get_return_link(self, *args, **kwargs):
        return "{}search?id={}".format(
            _get_return_link(self.mode), ",".join(id for id in self.ids),
        )

    def get(self, *args, **kwargs):
        if not settings.ASSETS_REPORTS['ENABLE']:
            messages.error(self.request, _("Assets reports is disabled"))
            return HttpResponseRedirect(_get_return_link(self.mode))
        error = False
        try:
            self.template_file = ReportOdtSource.objects.get(
                slug=settings.ASSETS_REPORTS['INVOICE_REPORT']['SLUG'],
            )
        except ReportOdtSource.DoesNotExist:
            messages.error(self.request, _("Odt template does not exist!"))
            error = True
        self.ids = self.request.GET.getlist('select')
        self.assets = Asset.objects.filter(pk__in=self.ids)
        asset_distinct = self.assets.values(
            'invoice_no', 'invoice_date', 'provider'
        ).distinct()
        if asset_distinct.count() != 1:
            self.show_unique_error_message()
            error = True
        if not all(asset_distinct[0].viewvalues()):
            messages.error(self.request, _(
                "Asset invoice number, invoice date or provider can not be empty"
            ))
            error = True
        if error:
            return HttpResponseRedirect(self.get_return_link())
        # generate invoice report
        pdf_data = self.get_pdf_content()
        if not pdf_data:
            return HttpResponseRedirect(self.get_return_link())
        response = HttpResponse(content=pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.file_name,
        )
        return response

    def get_pdf_content(self, *args, **kwargs):
        content = None
        data = self.get_report_data()
        self.file_name = '{}-{}-{}.pdf'.format(
            self.template_file.slug,
            data['id'],
            uuid.uuid4(),
        )
        output_path = '{}{}'.format(
            settings.ASSETS_REPORTS['TEMP_STORAGE_PATH'],
            self.file_name,
        )
        generate_pdf(
            self.template_file.template.path,
            output_path,
            data,
        )
        try:
            with open(output_path, 'rb') as f:
                content = f.read()
                f.close()
        except IOError as e:
            logger.error(
                "Can not read report for assets ids: {} ({})".format(
                    ",".join(id for id in self.ids), e,
                )
            )
            messages.error(self.request, _(
                "The error occurred, was not possible to read generated file."
            ))
        return content

    def get_report_data(self, *args, **kwargs):
        first_asset = self.assets[0]
        data = {
            "id": slugify(first_asset.invoice_no),
            "base_info": {
                "invoice_no": first_asset.invoice_no,
                "invoice_date": first_asset.invoice_date,
                "provider": first_asset.provider,
                "datetime": datetime.datetime.now(),
            },
            "assets": self.assets,
        }
        return data


class AddAttachment(AssetsBase):
    template_name = 'assets/add_attachment.html'
    sidebar_selected = None

    def get_context_data(self, **kwargs):
        ret = super(AddAttachment, self).get_context_data(**kwargs)
        ret.update({
            'formset': self.attachments_formset,
        })
        return ret

    def get(self, *args, **kwargs):
        url_assets_ids = self.request.GET.getlist('select')
        assets = Asset.objects.filter(pk__in=url_assets_ids)
        if not assets.exists():
            messages.warning(self.request, _("Nothing to edit."))
            return HttpResponseRedirect(_get_return_link(self.mode))

        AttachmentFormset = formset_factory(
            form=AttachmentForm, extra=1
        )
        self.attachments_formset = AttachmentFormset()
        return super(AddAttachment, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        url_assets_ids = self.request.GET.getlist('select')
        assets = Asset.objects.filter(id__in=url_assets_ids)
        AttachmentFormset = formset_factory(
            form=AttachmentForm, extra=0
        )
        self.attachments_formset = AttachmentFormset(
            self.request.POST, self.request.FILES
        )
        if self.attachments_formset.is_valid():
            for form in self.attachments_formset.forms:
                instance = form.save(commit=False)
                instance.original_filename = instance.file.name
                instance.save()
                for asset in assets:
                    asset.attachments.add(instance)
            messages.success(self.request, _("Changes saved."))
            return HttpResponseRedirect(_get_return_link(self.mode))
        messages.error(self.request, _("Please correct the errors."))
        return super(AddAttachment, self).get(*args, **kwargs)
