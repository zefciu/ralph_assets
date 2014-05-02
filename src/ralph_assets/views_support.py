# -*- coding: utf-8 -*-

from ralph_assets.forms_support import (
    SupportForm,
    SupportSearchForm,
)
from ralph_assets.models_support import Support
from ralph_assets.views import (
    AssetsBase,
    GenericSearch,
)
from bob.data_table import DataTableColumn
from ralph_assets.models_assets import MODE2ASSET_TYPE
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from ralph_assets.views_sam import CheckBoxColumn


class SupportLinkColumn(DataTableColumn):
    """A column that links to the edit page of a support simply displaying
    'Support' in a grid"""
    def render_cell_content(self, resource):
        return '<a href="{url}">{support}</a>'.format(
            url=resource.url,
            support=unicode(_('Support')),
        )


class SupportFormView(AssetsBase):
    """Base view that displays support form."""

    template_name = 'assets/add_support.html'
    sidebar_selected = None

    def _get_form(self, data=None, **kwargs):
        self.form = SupportForm(
            mode=self.mode, data=data, **kwargs
        )

    def get_context_data(self, **kwargs):
        ret = super(SupportFormView, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_support_form',
            'edit_mode': False,
            'caption': self.caption,
            'support': getattr(self, 'support', None),
            'mode': self.mode,
        })
        return ret

    def _save(self, request, *args, **kwargs):
        try:
            support = self.form.save(commit=False)
            if support.asset_type is None:
                support.asset_type = MODE2ASSET_TYPE[self.mode]
            support.save()
            self.form.save_m2m()
            messages.success(self.request, self.message)
            return HttpResponseRedirect(support.url)
        except ValueError:
            return super(SupportFormView, self).get(request, *args, **kwargs)



class AddSupportForm(SupportFormView):
    """Add a new support"""

    caption = _('Add Support')
    mainmenu_selected = 'supports'
    message = _('Support added')
    Form = SupportForm

    def get(self, request, *args, **kwargs):
        self._get_form()
        return super(AddSupportForm, self).get(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._get_form(request.POST)
        if self.form.is_valid():
            self.form.instance.pk = None
            support = self.form.save(commit=False)
            if support.asset_type is None:
                support.asset_type = MODE2ASSET_TYPE[self.mode]
            support.save()
            messages.success(self.request, self.message)
            return HttpResponseRedirect(reverse('support_list'))
        else:
            return super(AddSupportForm, self).get(request, *args, **kwargs)



class SupportList(GenericSearch):
    """The support list."""

    mainmenu_selected = 'supports'
    Form = SupportSearchForm
    Model = Support
    
    columns = [
        CheckBoxColumn(
            _('Dropdown'),
            selectable=True,
            bob_tag=True,
        ),
        SupportLinkColumn(
            _('Type'),
            bob_tag=True,
        ),
        DataTableColumn(
            _('Contract id'),
            bob_tag=True,
            field='contract_id',
            sort_expression='contract_id',
        ),
        DataTableColumn(
            _('Name'),
            bob_tag=True,
            field='name',
            sort_expression='name',
        ),
        DataTableColumn(
            _('Date from'),
            bob_tag=True,
            field='date_from',
            sort_expression='date_from',
        ),
        DataTableColumn(
            _('Date to'),
            bob_tag=True,
            field='date_to',
            sort_expression='date_to',
        ),
        DataTableColumn(
            _('Cost'),
            bob_tag=True,
            field='cost',
            sort_expression='cost',
        ),             
    ]

    def get_context_data(self, *args, **kwargs):
        data = super(SupportList, self).get_context_data(
            *args, **kwargs
        )
        if self.mode:
            data['supports'] = Support.objects.filter(
                asset_type=MODE2ASSET_TYPE[self.mode],
            )
        else:
            data['supports'] = Support.objects.all()
        return data


class EditSupportForm(SupportFormView):
    """Edit support"""

    caption = _('Edit Support')
    message = _('Support changed')
    Form = SupportForm

    def get(self, request, support_id, *args, **kwargs):
        #import sys; sys.path.append('/data/src/pydev')
        #import pydevd; pydevd.settrace(host='localhost', port=5678)
        self.support = Support.objects.get(pk=support_id)
        self._get_form(instance=self.support)
        return super(EditSupportForm, self).get(request, *args, **kwargs)

    def post(self, request, support_id, *args, **kwargs):
        self.support = Support.objects.get(pk=support_id)
        self._get_form(request.POST, instance=self.support)
        return self._save(request, *args, **kwargs)
    

class DeleteSupportForm(AssetsBase):
    """Delete a support."""

    def post(self, *args, **kwargs):
        record_id = self.request.POST.get('record_id')
        try:
            support = Support.objects.get(pk=record_id)
        except Asset.DoesNotExist:
            messages.error(self.request, _("Selected asset doesn't exists."))
            return HttpResponseRedirect(_get_return_link(self.mode))
        self.back_to = reverse(
            'support_list',
            kwargs={'mode': ASSET_TYPE2MODE[support.asset_type]},
        )
        support.delete()
        return HttpResponseRedirect(self.back_to)
