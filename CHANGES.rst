Change Log
----------

1.2.13
~~~~~~~

* fixes of Discovered column. Also it shows now on csv reports.

1.2.12
~~~~~~~

* Improved the csv exporting system

1.2.11
~~~~~~~

* Basing deprecation on invoice date instead of delivery date

1.2.10
~~~~~~~~~~~

* Pricing api uses only devices that existed on given date

* Pricing api can use forced deprecation

1.2.9
~~~~

* Merged the u_height and size attributes

* Dynamically requiring 'slots' for blade categories

* Fixed unit tests

1.2.7
~~~~~
Released on October 03, 2013

* Added API for Ralph.

* Required form fields are now labelled accordingly.

* ``ralph_device_id`` get automatically cleaned when when Device linked to it gets deleted.

* Added partial and exact searches to assets.

* Unlinking assets from devices (and searching for unlinked assets) is now
  possible.

* Added searching assets by ``ralph_device_id``. Added option to create stock
  devices for unlinked assets.

* Fixed creating assets with ``add part`` button.

* Column ``department`` added to csv report in ``search DC assets``.



1.2.6
~~~~~

Released on August 08, 2013

* Added ajax autocomlation for Asset by barcode and/or sn.

* Disabled admin deletetion for Assets.

* Added link to the Pricing App.

* Added field: last modification, asset_id to csv file.



1.0.0
~~~~~

* initial release
