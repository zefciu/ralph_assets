# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from bob.menu import MenuItem, MenuHeader

from ralph_assets.views.base import AssetsBase
from ralph_assets.models_assets import Asset


logger = logging.getLogger(__name__)


class CategoryModelReport(object):
    slug = 'category-model'
    name = _('Category - model')

    def execute(self):
        pass


reports = [CategoryModelReport, ]


class ReportViewBase(AssetsBase):
    mainmenu_selected = 'reports'

    def get_sidebar_items(self, base_sidebar_caption):
        sidebar_menu = [MenuHeader(_('Available reports'))] + [
            MenuItem(label=r.name, href=reverse('report', args=(r.slug,)))
            for r in reports
        ]
        sidebar_menu.extend(super(ReportViewBase, self).get_sidebar_items(
            base_sidebar_caption
        ))
        return sidebar_menu


class ReportsList(ReportViewBase):
    pass


class ReportDetail(ReportViewBase):
    def get_context_data(self, *args, **kwargs):
        ret = super(ReportDetail, self).get_context_data(**kwargs)
        report_dict = {}
        ret.update({'report_dict': report_dict})
        return ret
