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

    Bulk.prototype.invoice_report = function() {
        var ids = this.get_ids();
        if (ids.length){
            window.location.href = 'invoice_report?select=' + ids.join('&select=');
        }
    };

    Bulk.prototype.add_attachment = function() {
        var ids = this.get_ids();
        if (ids.length){
            window.location.href = 'add_attachment?select=' + ids.join('&select=');
        }
    };

    $(document).ready(function() {
        var bulk = new Bulk();
        $('#post_edit_all').click(function() {
            bulk.edit_selected();
        });

        $('#post_invoice_report').click(function() {
            bulk.invoice_report();
        });

        $('#post_add_attachment').click(function() {
            bulk.add_attachment();
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
