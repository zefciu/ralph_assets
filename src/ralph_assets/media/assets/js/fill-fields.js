  // Fill fields in bulk edit and cleave asset forms

  // Disable autocomplete without cluttering html attributes
  $('input').attr('autocomplete', 'off');

  /* After closing datepicker toogle toolbar */
  $('.datepicker').on('changeDate', function (ev) {
      toggle_toolbar(this);
  });

  $("input[type=text].fillable,select.fillable").blur(function (event) {
      $("#float_toolbar").hide();
  });

  var toggle_toolbar = function (input) {
      var toolbar = $("#float_toolbar");
      var offset = $(input).offset();
      var width = input.clientWidth;
      var height = input.clientHeight;
      var distance_left = 0;
      var distance_top = 0;

      /* Clear data */
      $(toolbar).data('input_name', '');
      $(toolbar).data('input_id', '');

      /* For fields without id set, save its name as selector */
      if (input.id === '') {
          $(toolbar).data('input_name', input.name);
      } else {
          $(toolbar).data('input_id', input.id);
      }
      toolbar.css("left", parseInt(offset.left) + width + distance_left + "px");
      toolbar.css("top", parseInt(offset.top) + height + distance_top + "px");
      toolbar.show();
  }

  $("input[type=text].fillable,select.fillable").focus(function (event) {
      toggle_toolbar(this);
  });

  $("#fill_all_rows").mousedown(function (event) {
      var MAX_ROWS = 100;
      var input_id = $("#float_toolbar").data('input_id');
      var input_name = $("#float_toolbar").data('input_name');
      var matcher = /(.*)-([0-9]+)-(.*)/;
      var results, pre, number, post, value_to_fill, el;
      if (input_id != '') {
          results = matcher.exec(input_id);
          value_to_fill = $('#' + input_id).val();
      } else if (input_name != '') {
          results = matcher.exec(input_name);
          value_to_fill = $('input[name="' + input_name + '"]').val();
      }

      pre = results[1];
      number = results[2];
      post = results[3];
      for (var i = 0; i < MAX_ROWS; i++) {
          if (input_id != '') {
              el = $('#' + pre + "-" + i + "-" + post);
          } else {
              el = $('input[name="' + pre + "-" + i + "-" + post + '"]');
          }
          if (!el.length) {
              break;
          }
          el.val(value_to_fill);
      }
      $("#float_toolbar").hide();
      return false;
  });
