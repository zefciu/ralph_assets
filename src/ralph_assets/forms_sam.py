"""Forms for SAM module."""

from django import forms

from ralph_assets import models_sam


class LicenceForm(forms.ModelForm):
    """Licence add/edit form for licences."""

    def __init__(self, mode, *args, **kwargs):
        self.mode = mode
        super(LicenceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models_sam.Licence
        fields = (
            'manufacturer',
            'licence_type',
            'software_category',
            'number_bought',
            'sn',
            'parent',
            'niw',
            'bought_date',
            'valid_thru',
            'order_no',
            'price',
            'accounting_id',
            'used',
        )
        widgets = {}
