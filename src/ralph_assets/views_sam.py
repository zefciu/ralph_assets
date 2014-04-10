import urllib

from bob.data_table import DataTableColumn
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
        DataTableColumn(
            'Software Category',
            bob_tag=True,
            field='software_category',
            sort_expression='software_category__name',
        )
    ]
