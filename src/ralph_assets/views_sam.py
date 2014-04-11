import urllib

from bob.data_table import DataTableColumn
from django.utils.translation import ugettext_lazy as _
from ralph_assets.views import GenericSearch, DataTableColumnAssets
from ralph_assets.models_sam import SoftwareCategory, Licence
from ralph_assets.forms_sam import (
    SoftwareCategorySearchForm,
    LicenceSearchForm,
)


class SoftwareCategoryNameColumn(DataTableColumn):
    """A column with software category name linking to the search of
    licences"""

    def render_cell_content(self, resource):
        name = super(SoftwareCategoryNameColumn, self).render_cell_content(resource)
        return '<a href="/assets/sam/licences/?{qs}">{name}</a>'.format(
            qs=urllib.urlencode({'software_category': resource.id}),
            name=name,
        )

class LicenceLinkColumn(DataTableColumn):
    """A column that links to the edit page of a licence simply displaying
    'Licence' in a grid"""
    def render_cell_content(self, resource):
        return '<a href="{url}">{licence}</a>'.format(
            url = resource.url,
            licence = unicode(_('Licence')),
        )




class SoftwareCategoryList(GenericSearch):
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


class LicenceList(GenericSearch):
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
            field='bought_date',
            sort_expression='bought_date',
        ),
        DataTableColumn(
            _('Valid thru'),
            bob_tag=True,
            field='valid_thru',
            sort_expression='valid_thru',
        ),

    ]
