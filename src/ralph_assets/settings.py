DEFAULT_DEPRECATION_RATE = 25

ASSETS_REPORTS = {
    'ENABLE': False,
    'INVOICE_REPORT': {'SLUG': 'invoice-report'},
    'RELEASE-ASSET': {'SLUG': 'release-asset'},
    'LOAN-ASSET': {'SLUG': 'loan-asset'},
    'RETURN-ASSET': {'SLUG': 'return-asset'},
    'TEMP_STORAGE_PATH': '/tmp/',
}

ASSETS_TRANSITIONS = {
    'ENABLE': False,
    'SLUGS': {
        'RELEASE-ASSET': 'release-asset',
        'LOAN-ASSET': 'loan-asset',
        'RETURN-ASSET': 'return-asset',
    }
}

ASSET_HIDE_ACTION_SEARCH = False
