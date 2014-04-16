# -*- coding: utf-8 -*-
"""The pluggable app definitions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.app import RalphModule


class Assets(RalphModule):
    """Assets main application."""

    url_prefix = 'assets'
    module_name = 'ralph_assets'
    disp_name = 'Assets'
    icon = 'fugue-box-label'

    def __init__(self, **kwargs):
        super(Assets, self).__init__(
            'ralph_assets',
            distribution='ralph_assets',
            **kwargs
        )
        self.append_app()
        self.insert_templates(__file__)
        self.register_logger('ralph_assets', {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        })
        self.settings['DEFAULT_DEPRECATION_RATE'] = 25
        self.settings['ASSETS_REPORTS'] = {
            'ENABLE': False,
            'INVOICE_REPORT': {'SLUG': 'invoice-report'},
            'RELEASE-ASSET': {'SLUG': 'release-asset'},
            'LOAN-ASSET': {'SLUG': 'loan-asset'},
            'RETURN-ASSET': {'SLUG': 'return-asset'},
            'TEMP_STORAGE_PATH': '/tmp/',
        }
        self.settings['ASSETS_TRANSITIONS'] = {
            'ENABLE': False,
            'SLUGS': {
                'RELEASE-ASSET': 'release-asset',
                'LOAN-ASSET': 'loan-asset',
                'RETURN-ASSET': 'return-asset',
            },
        }
        self.settings.setdefault("ASSET_HIDE_ACTION_SEARCH", False)
