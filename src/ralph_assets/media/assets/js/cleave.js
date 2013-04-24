$(document).ready(function() {
    var FORM_COUNT = parseInt($('input[name="form-TOTAL_FORMS"]').val());

    $('.add_row').on("click", function(){
        var row = $('.form-cleave tr').last().clone(true, true);
        row.find('input').each(function(i, elem) {
            $(elem).val('');
            td_class = $(elem).parent().attr('class');
            td_class = td_class.replace('error', '');
            $(elem).parent().attr('class', td_class);

        });
        row.find('.help-inline').remove();
        row.find('.uneditable-input').html('');
        row.appendTo(".form-cleave tbody");
        FORM_COUNT +=1;
        $('input[name="form-TOTAL_FORMS"]').val(FORM_COUNT);
        $('input[name="form-INITIAL_FORMS"]').val(FORM_COUNT);
        renumber_forms();
        return false;
    });

    $("body").delegate(".form-cleave .delete_row", "click", function(){
        var row_count = $('.form-cleave tr').length;
        console.log(row_count);
        if(row_count >=3){
            $(this).parents('tr').remove();
        }
        FORM_COUNT -=1;
        $('input[name="form-TOTAL_FORMS"]').val(FORM_COUNT);
        $('input[name="form-INITIAL_FORMS"]').val(FORM_COUNT);
        renumber_forms();
        return false;
    });

    $(".input, .uneditable-input").on("click", function(){
        $(this).parent().next("td").find('input').val($(this).html());
    });

    function renumber_forms()
    {
        var form = $('.form-cleave tr')
        form.each(function(i, elem){
             $(elem).find('input').each(function(j, elem){
                 var numberPattern = /\d+/g;
                 name = $(elem).attr('name');
                 $(elem).attr('name', name.replace(numberPattern, i-1));
            });
        });

        $('.ordinal').each(function(i, elem){
            console.log($(elem).html(i+1));
        });
    }
});
