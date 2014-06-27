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

# force locale during pdf raport genration
GENERATED_DOCS_LOCALE = None

ASSET_HOSTNAME_TEMPLATE = {
    'prefix': '{{ object.country_code|upper }}'
              '{{ object.model.category.code|upper }}',
    'postfix': '',
    'counter_length': 5,
}
