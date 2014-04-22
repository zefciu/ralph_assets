# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib

from bob.data_table import DataTableColumn
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from ralph_assets.models_history import LicenceHistoryChange
from ralph_assets.models_sam import (
    Licence,
    SoftwareCategory,
)
from ralph_assets.forms_sam import (
    SoftwareCategorySearchForm,
    LicenceSearchForm,
)
from ralph_assets.views import (
    AssetsBase,
    GenericSearch,
    LicenseSelectedMixin,
    HISTORY_PAGE_SIZE,
    MAX_PAGE_SIZE,
)


class SoftwareCategoryNameColumn(DataTableColumn):
    """A column with software category name linking to the search of
    licences"""

    def render_cell_content(self, resource):
        name = super(
            SoftwareCategoryNameColumn, self
        ).render_cell_content(resource)
        return '<a href="/assets/sam/licences/?{qs}">{name}</a>'.format(
            qs=urllib.urlencode({'software_category': resource.id}),
            name=name,
        )


class LicenceLinkColumn(DataTableColumn):
    """A column that links to the edit page of a licence simply displaying
    'Licence' in a grid"""
    def render_cell_content(self, resource):
        return '<a href="{url}">{licence}</a>'.format(
            url=resource.url,
            licence=unicode(_('Licence')),
        )


class SoftwareCategoryList(LicenseSelectedMixin, GenericSearch):
    """Displays a list of software categories, which link to searches for
    licences."""

    Model = SoftwareCategory
    Form = SoftwareCategorySearchForm
    columns = [
        SoftwareCategoryNameColumn(
            'Name',
            bob_tag=True,
            field='name',
            sort_expression='name',
        ),
    ]


class LicenceList(LicenseSelectedMixin, GenericSearch):
    """Displays a list of licences."""

    Model = Licence
    Form = LicenceSearchForm
    columns = [
        LicenceLinkColumn(
            _('Type'),
            bob_tag=True,
        ),
        DataTableColumn(
            _('Inventory number'),
            bob_tag=True,
            field='niw',
            sort_expression='niw',
        ),
        DataTableColumn(
            _('Licence Type'),
            bob_tag=True,
            field='licence_type__name',
            sort_expression='licence_type__name',
        ),
        DataTableColumn(
            _('Manufacturer'),
            bob_tag=True,
            field='manufacturer__name',
            sort_expression='manufacturer__name',
        ),
        DataTableColumn(
            _('Software Category'),
            bob_tag=True,
            field='software_category',
            sort_expression='software_category__name',
        ),
        DataTableColumn(
            _('Property of'),
            bob_tag=True,
            field='property_of__name',
            sort_expression='property_of__name',
        ),
        DataTableColumn(
            _('Number of purchased items'),
            bob_tag=True,
            field='number_bought',
            sort_expression='number_bought',
        ),
        DataTableColumn(
            _('Used'),
            bob_tag=True,
            field='used',
        ),
        DataTableColumn(
            _('Invoice date'),
            bob_tag=True,
            field='invoice_date',
            sort_expression='invoice_date',
        ),
        DataTableColumn(
            _('Valid thru'),
            bob_tag=True,
            field='valid_thru',
            sort_expression='valid_thru',
        ),

    ]


class HistoryLicence(AssetsBase):
    template_name = 'assets/history.html'

    def get_context_data(self, **kwargs):
        query_variable_name = 'history_page'
        ret = super(HistoryLicence, self).get_context_data(**kwargs)
        licence_id = kwargs.get('licence_id')
        licence = Licence.objects.get(id=licence_id)
        history = LicenceHistoryChange.objects.filter(
            licence=licence,
        ).order_by('-date')
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
            'show_status_button': False,
            'query_variable_name': query_variable_name,
            'object': licence,
            'object_url': reverse(
                'edit_licence',
                kwargs={
                    'licence_id': licence.id,
                    'mode': self.mode,
                }
            ),
            'title': _('History licence'),
        })
        return ret
