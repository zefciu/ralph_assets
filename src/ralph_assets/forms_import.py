"""Utilities for using forms to upload tabular data."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import csv
import xlrd
import itertools as it

from django import forms

class DataUploadField(forms.FileField):
    """A field that gets the uploaded XLS or CSV data and returns data
    prepared for add/update."""

    def _process_xls(self, file_):
        book = xlrd.open_workbook(
            filename=file_.name,
            file_contents=file_.read(),
        )
        names_per_sheet = {}
        update_per_sheet = {}
        add_per_sheet = {}
        for sheet_name, sheet in (
            (sheet_name, book.sheet_by_name(sheet_name)) for
            sheet_name in book.sheet_names()
        ):
            if not sheet:
                continue
            name_row = sheet.row(0)
            update = name_row[0].value == 'id'
            if update:
                name_row = name_row[1:]
            names_per_sheet[sheet_name] = col_names = [
                cell.value for cell in name_row[:]
            ]
            update_per_sheet[sheet_name] = {}
            add_per_sheet[sheet_name] = []
            if update:
                for row in (sheet.row(i) for i in xrange(1, sheet.nrows)):
                    asset_id = int(row[0].value)
                    update_per_sheet[sheet_name][asset_id] = {}
                    for key, cell in it.izip(col_names, row[1:]):
                        update_per_sheet[sheet_name][asset_id][key] = cell.value
            else:
                for row in (sheet.row(i) for i in xrange(1, sheet.nrows)):
                    asset_data = {}
                    add_per_sheet[sheet_name].append(asset_data)
                    for key, cell in it.izip(col_names, row):
                        asset_data[key] = cell.value

        return names_per_sheet, update_per_sheet, add_per_sheet

    def _process_csv(self, file_):
        reader = csv.reader(file_)
        update_per_sheet = {'csv': {}}
        add_per_sheet = {'csv': []}
        name_row = next(reader)
        update = name_row[0] == 'id'
        if update:
            name_row = name_row[1:]
            for row in reader:
                asset_id = int(row[0])
                update_per_sheet['csv'].setdefault(asset_id, {})
                for key, value in it.izip(name_row, row[1:]):
                    update_per_sheet['csv'][asset_id][key] = value
        else:
            for row in reader:
                asset_data = {}
                add_per_sheet['csv'].append(asset_data)
                for key, value in it.izip(name_row, row[:]):
                    asset_data[key] = value
                
        names_per_sheet = {'csv': name_row}
        
        return names_per_sheet, update_per_sheet, add_per_sheet

    def to_python(self, value):
        file_ = super(DataUploadField, self).to_python(value)
        try:
            filetype = {
                'application/vnd.openxmlformats-officedocument.'
                    'spreadsheetml.sheet': 'xls',
                'text/csv': 'csv',
                'application/csv': 'csv',
            }[file_.content_type]
        except KeyError:
            raise forms.ValidationError(
                'Unsupported file type. Use CSV of Excel.'
            )
        return (
            self._process_xls if filetype == 'xls' else self._process_csv
        )(file_)
