# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from ralph_assets.forms_transitions import TransitionForm
from ralph_assets.views import _AssetSearch
from ralph_assets.models import ReportOdtSource, Transition, TransitionsHistory


class TransitionDispatcher(object):
    """
    Handling actions defined in the transition.
    Available actions:
    - assign_user - assign user to assets.
    - change_status - change assets status to definied in Transition.
    - release_report - generate release assets report file.
    - return_report - generate return assets report file.
    """

    def __init__(
        self,
        instance,
        transition,
        assets,
        logged_user,
        affected_user,
        template_file=None,
    ):
        self.instance = instance
        self.transition = transition
        self.assets = assets
        self.logged_user = logged_user
        self.affected_user = affected_user
        self.template_file = template_file
        self.report_file_patch = None

    def _action_assign_user(self):
        for asset in self.assets:
            asset.user = self.user
            asset.save()

    def _action_change_status(self):
        for asset in self.assets:
            asset.status = self.transition.to_status
            asset.save()

    def _generate_report(self, type):
        pass

    def _action_release_report(self,):
        return self.report_file_patch

    def _action_return_report(self,):
        return self.report_file_patch

    def _save_history(self):
        TransitionsHistory.create(dict(
            transition=self.transition,
            assets=self.assets,
            logged_user=self.logged_user,
            affected_user=self.affected_user,
        ))

    def get_report_file_patch(self):
        return self.report_file_patch

    def run(self):
        actions = self.transition.actions_names()
        if 'assign_user' in actions:
            self._action_assign_user()
        if 'change_status' in actions:
            self._action_change_status()
        if 'release_report' in actions:
            self._action_release_report()
        elif 'return_report' in actions:
            self._action_return_report()
        self._save_history()


class TransitionView(_AssetSearch):
    template_name = 'assets/transitions.html'
    report_file_path = None

    def get_transition_object(self, *args, **kwargs):
        try:
            transition = Transition.objects.get(
                slug=settings.ASSETS_TRANSITIONS['SLUGS'][
                    self.transition_type.upper()
                ]
            )
            self.assign_user = 'assign_user' in transition.actions_names()
        except Transition.DoesNotExist:
            transition = None
        return transition

    def get_transition_form(self, *args, **kwargs):
        form = TransitionForm(self.request.POST)
        if not self.assign_user:
            form.fields.pop('user')
        return form

    def get_assets(self, *args, **kwargs):
        if self.request.GET.get('from_query'):
            all_q = super(
                TransitionView, self,
            ).handle_search_data(*args, **kwargs)
        else:
            all_q = Q(pk__in=self.ids)
        return self.get_all_items(all_q)

    def get_affected_user(self, *args, **kwargs):
        if 'return_report' in self.transition_object.actions_names():
            affected_user = self.asset[0].user
        else:
            affected_user = self.form.instance.user
        return affected_user

    def check_reports_template_exists(self, *args, **kwargs):
        try:
            self.template_file = ReportOdtSource.object.get(
                slug=settings.ASSETS_REPORTS[
                    self.transition_type.upper(),
                ]['SLUG'],
            )
            valid = True
        except ReportOdtSource.DoesNotExist:
            messages.error(self.request, _("Odt template does not exist!"))
            valid = False
        return valid

    def error_handler(self, *args, **kwargs):
        error = False
        if not settings.ASSETS_TRANSITIONS['ENABLE']:
            messages.error(self.request, _("Assets transitions is disabled"))
            error = True
        self.transition_type = self.request.GET.get('transition_type')
        if self.transition_type not in [
            'release-asset', 'return-asset', 'loan-asset',
        ]:
            messages.error(self.request, _("Unsupported transition type"))
            error = True
        error = self.check_reports_template_exists()
        self.transition_object = self.get_transition_object()
        if not self.transition_object:
            messages.error(self.request, _("Transition object not found"))
            error = True
        if self.assign_user:
            assets = self.assets.values_list('user__username').distinct()
            if assets.count() != 1:
                messages.error(
                    self.request,
                    _(
                        'Asset has different user: {}'.format(
                            ", ".join(asset[0] for asset in assets)
                        )
                    ),
                )
                error = True
        return error

    def get(self, *args, **kwargs):
        self.assets = self.get_assets()
        errors = self.error_handler()
        if errors:
            pass
            # return HttpResponseRedirect(_get_return_link(self.mode))
        self.form = self.get_transition_form()
        return super(TransitionView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.assets = self.get_assets()
        errors = self.error_handler()
        if errors:
            pass  # to sie dopisze :)
        self.form = self.get_transition_form()
        if self.form.is_valid():
            dispatcher = TransitionDispatcher(
                self,
                self.transition_object,
                self.assets,
                self.request.user,
                self.get_affected_user(),
            )
            dispatcher.run()
            self.report_file_path = dispatcher.report_file_patch()
            # return HttpResponseRedirect(_get_return_link(self.mode))
        messages.error(self.request, _('Please correct errors.'))
        return super(TransitionView, self).get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(TransitionView, self).get_context_data(**kwargs)
        ret.update({
            'report_file_path': self.report_file_path,
            'assets': self.assets,
            'transition_form': self.form,
            'transition_type': self.transition_type.replace('-', ' ').title(),
        })
        return ret
