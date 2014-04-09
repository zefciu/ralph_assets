from ralph_assets.views import GenericSearch, DataTableColumnAssets
from ralph_assets.models_sam import SoftwareCategory
from ralph_assets.forms_sam import SoftwareCategorySearchForm



class SoftwareCategoryList(GenericSearch):
    """Displays a list of software categories, which link to searches for
    licences."""

    Model = SoftwareCategory
    Form = SoftwareCategorySearchForm
    _ = DataTableColumnAssets
    columns = [
        _(
            'Name',
            bob_tag=True,
            field='name',
            sort_expression='name',
        ),
    ]
