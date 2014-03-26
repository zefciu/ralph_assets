Transitions
===========

Give the opportunity to take advantage of the transition, which facilitating multi-changes in assets including generation report file.

Configurations
~~~~~~~~~~~~~~

Default transition is disabled. To enable, set variables in settings::

    ASSETS_TRANSITIONS['ENABLE'] = True

You must add transition object in database. Actually we supported following transitions: ``RELEASE-ASSET``, ``LOAN-ASSET``, ``RETURN-ASSET``.

Each transition have default slug defined in settings. You may nothing changed in settings and use predefined slugs in transition definition objects.

To change slugs update settings variable eg.::

    ASSETS_TRANSITIONS['SLUGS']['RELEASE'] = "your-custom-slug"

Default slugs:

    * ``release-asset`` - for ``RELEASE-ASSET`` transition
    * ``loan-asset`` - for ``LOAN-ASSET`` transition
    * ``return-asset`` - for ``RETURN-ASSET`` transition

Actions available in transitions:

    * ``assign_user`` - assign new user into assets.
    * ``assign_warehouse`` - assign new warehouse into assets.
    * ``change_status`` - change status into defined in ``to_status`` Transition field.
    * ``release_report`` - generate release report file.
    * ``return_report`` - generate return report file.
    * ``unassign_user`` - remove user assigned into assets.

Reports
-------

To be generate reports file, should be uploaded report template file into 'Report odt source' model. Created model should be specified slug.
And configure `INKPY <https://pypi.python.org/pypi/inkpy>`_  module.

Slug definition per report may be overridden in settings file eg.::

    ASSETS_REPORTS['RELEASE-ASSET']['SLUG'] = 'your-slug'

You can use predefined slugs:

    * ``release-asset`` - for release asset transition
    * ``loan-asset`` - for loan asset transition
    * ``return-asset`` - for return asset transition

