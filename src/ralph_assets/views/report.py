# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.http import Http404

from bob.menu import MenuItem, MenuHeader

from ralph_assets.views.base import AssetsBase
from ralph_assets.models_assets import Asset, AssetCategory, AssetModel


logger = logging.getLogger(__name__)


class CategoryModelReport(object):
    slug = 'category-model'
    name = _('Category - model')

    def execute(self):
        from collections import defaultdict
        queryset = AssetCategory.objects.filter(parent=None)
        result = []
        # aggr = defaultdict(int)
        for row in queryset:
            print()
            result.append({
                'count': row.assetmodel_set.count(),
                'name': row.name,
                'extra': row.get_ancestors(),
            })

        return result


class ReportViewBase(AssetsBase):
    mainmenu_selected = 'reports'
    reports = [CategoryModelReport, ]

    def get_sidebar_items(self, base_sidebar_caption):
        sidebar_menu = [MenuHeader(_('Available reports'))] + [
            MenuItem(label=r.name, href=reverse('report', args=(r.slug,)))
            for r in self.reports
        ]
        sidebar_menu.extend(super(ReportViewBase, self).get_sidebar_items(
            base_sidebar_caption
        ))
        return sidebar_menu


class ReportsList(ReportViewBase):
    pass


class ReportDetail(ReportViewBase):

    template_name = 'assets/report_detail.html'

    def get_report(self, slug):
        for report in self.reports:
            if report.slug == slug:
                return report()
        return None

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        self.report = self.get_report(slug)
        if not self.report:
            raise Http404
        return super(ReportDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(ReportDetail, self).get_context_data(**kwargs)
        context_data.update({
            'report': self.report,
            'subsection': self.report.name,
            'result': self.report.execute(),
        })
        return context_data
