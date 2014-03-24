(function(){
    "use strict";

    var Bulk = function () {};

    Bulk.prototype.get_ids = function(){
        var ids = [];
        $("#assets_table input[type=checkbox]").each(
            function(index, val){
                if(val.checked) {
                    ids.push($(val).val());
                };
            }
        );
        return ids;
    }

    Bulk.prototype.edit_selected = function() {
        var ids = this.get_ids();
        if (ids.length) {
            window.location.href = 'bulkedit?select=' + ids.join('&select=');
        }
        return false;
    };

    Bulk.prototype.invoice_report_selected = function() {
        var ids = this.get_ids();
        if (ids.length){
            window.location.href = 'invoice_report?select=' + ids.join('&select=');
        }
    };

    Bulk.prototype.addAttachment = function(type) {
        var ids = this.get_ids();
        if (ids.length){
            window.location.href = 'add_attachment/' + type + '/?select=' + ids.join('&select=');
        }
    };
    Bulk.prototype.invoice_report_search_query = function () {
        var params = window.location.search;
        if (params.length){
            window.location.href = 'invoice_report' + params + '&from_query=1';
        }
    };

    $(document).ready(function() {
        var bulk = new Bulk();
        $('#post_edit_all').click(function() {
            bulk.edit_selected();
        });
        $('#post_invoice_report_selected').click(function() {
            bulk.invoice_report_selected();
        });
        $('#post_invoice_report_search_query').click(function() {
            bulk.invoice_report_search_query();
        });

        $('#post_add_attachment').click(function() {
            bulk.addAttachment('asset');
        });

        $('.delete-attachment').click(function() {
            if (!confirm("Are you sure to delete Attachment(s)?")) {
                return false;
            }
            var delete_type = $(this).attr('data-delete-type');
            var form_id = '#' + $(this).attr('data-form-id');
            $(form_id).find("input[name='delete_type']").val(delete_type);
            $(form_id).submit();
        });

        $('.del-asset-btn').click(function() {
            if (!confirm("Are you sure to delete Asset?")) {
                return false;
            }
        });
        require(['reports'], function(reports) {
            reports.setup({
                trigger: $('.pagination').find('a').last(),
                progressBar: '#async-progress',
                etaEl: '#eta'
            });
        });
    });

})();
