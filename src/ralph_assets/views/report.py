# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.http import Http404

from bob.menu import MenuItem, MenuHeader

from ralph_assets.views.base import AssetsBase
from ralph_assets.models_assets import (
    Asset,
    MODE2ASSET_TYPE,
)


logger = logging.getLogger(__name__)


class ReportNode(object):

    def __init__(self, name, count=0, parent=None, children=[], **kwargs):
        self.name = name
        self.count = count
        self.parent = parent
        self.children = []
        self.kwargs = kwargs

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        child.update_count()

    def add_to_count(self, count):
        self.count += count

    def update_count(self):
        map(lambda x: x.add_to_count(self.count), self.ancestors)

    @property
    def ancestors(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def to_dict(self):
        return {
            'name': self.name,
            'count': self.count,
        }

    def __str__(self):
        return '{} ({})'.format(self.name, self.count)


class Report(list):

    def get(self, name):
        return next((x for x in self if x.name == name), None)

    def get_or_create(self, name):
        node = self.get(name)
        created = False
        if not node:
            node = ReportNode(name)
            self.append(node)
            created = True
        return node, created

    def add(self, name, count=0, parent=None):
        new_node = ReportNode(name, count)
        if parent:
            if not isinstance(parent, ReportNode):
                parent, _ = self.get_or_create(parent)
            parent.add_child(new_node)
        self.append(new_node)
        return new_node

    @property
    def roots(self):
        return [x for x in self if x.parent is None]

    @property
    def leafs(self):
        return [x for x in self if x.children == []]

    def to_dict(self):
        def traverse(node):
            ret = node.to_dict()
            ret['children'] = []
            for child in node.children:
                ret['children'].append(traverse(child))
            return ret
        return [traverse(root) for root in self.roots]


class ReportBase(object):
    def __init__(self):
        self.report = Report()

    def execute(self, mode):
        self.prepare(mode)
        return self.report.to_dict()

    def prepare(self, mode):
        raise NotImplemented()


class CategoryModelReport(ReportBase):
    slug = 'category-model'
    name = _('Category - model')

    def prepare(self, mode=None):
        qs = Asset.objects
        if mode:
            qs = qs.filter(type=mode)
        qs = qs.values(
            'model__category__name',
            'model__category__parent__name'
        ).annotate(num=Count('model'))

        for item in qs:
            self.report.add(
                name=item['model__category__name'],
                count=item['num'],
                parent=item['model__category__parent__name']
            )


class ReportViewBase(AssetsBase):
    mainmenu_selected = 'reports'
    reports = [CategoryModelReport]
    modes = ['dc', 'back_office', 'all']

    def get_sidebar_items(self, base_sidebar_caption):
        sidebar_menu = []
        for mode in self.modes:
            sidebar_menu += [MenuHeader(_('Reports {mode}'.format(mode=mode)))]
            sidebar_menu += [
                MenuItem(
                    label=r.name, href=reverse('report_detail', kwargs={
                        'mode': mode,
                        'slug': r.slug,
                    })
                )
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
        mode = kwargs.get('mode', 'all')
        if mode == 'all':
            self.asset_type = None
        else:
            self.asset_type = MODE2ASSET_TYPE[mode]
        self.report = self.get_report(slug)
        if not self.report:
            raise Http404
        return super(ReportDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(ReportDetail, self).get_context_data(**kwargs)
        context_data.update({
            'report': self.report,
            'subsection': self.report.name,
            'result': self.report.execute(self.asset_type),
        })
        return context_data
