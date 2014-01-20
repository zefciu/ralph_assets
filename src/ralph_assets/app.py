# -*- coding: utf-8 -*-
"""The pluggable app definitions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.app import RalphModule

class Assets(RalphModule):
    """Scrooge main application. The 'ralph_pricing' name is retained
    internally for historical reasons, while we try to use 'scrooge' as
    displayed name."""

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
