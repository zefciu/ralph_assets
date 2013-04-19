$(document).ready(function() {

    $('.add_row').on("click", function(){
        var row = $('.form-cleave tr').last().clone(true, true);
        var ordinal_container = $(row).find('.ordinal');
        var ordinal_no = $(ordinal_container).data("no");
        console.log(ordinal_no);
        ordinal_no++;
        ordinal_container.data("no", ordinal_no);
        ordinal_container.html(ordinal_no);
        row.find('input').each(function(i, elem) {
            var input_name = $(elem).attr('name');
            $(elem).attr('name', input_name.replace(ordinal_no-2, ordinal_no-1));
            $(elem).val('');
        });
        row.find('.uneditable-input').html('');
        row.appendTo(".form-cleave tbody");
        return false;
    });

    $("body").delegate(".form-cleave .delete_row", "click", function(){
        var row_count = $('.form-cleave tr').length;
        console.log(row_count);
        if(row_count >=3){
            $(this).parents('tr').remove();
        }
    });
});
