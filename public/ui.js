$(document).ready(function(){

  var connStateText = $("#conn-state-text");
  var commHistMax = 20;

  $.get("/isConnected").done(function(value) {
    str = value == 1 ? "Connected" : "Disconnected";
    connStateText.text(str);
  }).fail(function() {
    str = "Server connection error";
  });

  function appendToCmdHistory(str) {
    var i, j;

    console.log(str);

    var histdiv = $("#comm-msg-hist-list");

    if(!$.isArray(str)) {
      histdiv.append("<p>" + str + "</p>");
      return;
    }

    for(i = 0; i < str.length; i++) {
      for(j = 0; j < str[i]["msg"].length; j++) {
        histdiv.append("<p>" + str[i]["msg"][j] + "</p>");
        // if(histdiv.children().length > commHistMax) {
        //   histdiv.children(":first").remove();
        // }
      }
    }
    var length = histdiv.children().length;
    if(length > commHistMax) {
      histdiv.children().slice(0, length - commHistMax).remove();
    }
  }

  function isValidVSetPin(val) {
    return [3,9,10,11].indexOf(val) == -1;
  }

  function isValidVReadPin(val) {
    return [0,1,2,3].indexOf(val) == -1;
  }

  $("button#connect-button").click(function(){
    $.get("/connect").done(function(str){
      connStateText.text(str);
    });
  });

  $("button#reconnect-button").click(function(){
    $.get("/reconnect").done(function(str){
      connStateText.text(str);
    });
  });

  $("button#disconnect-button").click(function(){
    $.get("/disconnect").done(function(str){
      connStateText.text(str);
    });
  });

  $("button#comtest-button").click(function(){
    $.get("/serialComtest").done(function(str){
      appendToCmdHistory(str);
    });
  });

  $("button#vset-button").click(function(){
    var tocmdhist = function(){appendToCmdHistory("Invalid expression");}
    var text = $(".vset input[name=batch]").val();
    if(text == []){
      return;
    }
    text = text.trim();

    var parts = text.split(',');
    if(!$.isArray(parts)) {
      tocmdhist();
      return;
    }
    if(parts.length != 3) {
      tocmdhist();
      return;
    }
    var pins = parts[0].trim().split(' ').map(Number);
    if(pins.some(function(val){return isNaN(val);})) {
      tocmdhist();
      return;
    }
    if(pins.some(isValidVSetPin)) {
      appendToCmdHistory("Invalid pin");
      return;
    }
    var values = parts[1].trim().split(' ').map(Number);
    if(values.some(function(val){return isNaN(val);})) {
      tocmdhist();
      return;
    }
    if(values.some(function(val){return val>255 || val<0})){
      appendToCmdHistory("Invalid value");
      return;
    }
    if(values.length != pins.length) {
      tocmdhist();
      return;
    }
    var settling = Number(parts[2]);
    // console.log({pins:pins,values:values,settling:settling});
    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:JSON.stringify({pins:pins,values:values,settling:settling}),
      contentType: 'application/json'
      }).done(function(str){
        appendToCmdHistory(str);
      });
  });

  $(".vset table button").click(function(e){
    var button = $(e.target);
    var index = Number(button.attr("name"));
    var pins = [3, 9, 10, 11];
    var pin = pins[index];
    var value = $("input[name=value]", $(".vset table tr").eq(index+1)).val();
    value = Number(value);
    var settling = $("input[name=settling]", $(".vset table tr").eq(index+1)).val();
    settling = Number(settling);

    if(isNaN(value) || isNaN(settling)) return;

    // console.log({pins:[pin],values:[value],settling:settling});

    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:JSON.stringify({pins:[pin],values:[value],settling:settling}),
      contentType: 'application/json'
    }).done(function(str){
        appendToCmdHistory(str);
    });
  });

  $("button#vread-button").click(function(){
    var text = $(".vread input[name=batch]").val();
    if(text == []){
      return;
    }
    text = text.trim();

    var pins = text.split(' ').map(Number);

    if(pins.some(isValidVReadPin)) {
      appendToCmdHistory("Invalid pin");
      return;
    }
    if(pins.some(function(val){return isNaN(val);})) {
      appendToCmdHistory("Invalid expression");
      return;
    }
    // console.log({pins:pins});
    // this call is a must for sending arrays in json format
    $.ajax({
      url:'/serialVRead',
      method:'POST',
      data:JSON.stringify({pins:pins}),
      contentType: 'application/json'
      })
      .done(function(str){
        appendToCmdHistory(str);
        // console.log(str);
        lim = Math.min(str.length, 4);
        for(var i = 0; i < lim; i++) {
          // console.log("pin: " + pins[i]);
          // console.log("result: " + str[i]["data"]);
          $(".vread-value").eq(pins[i]).text(str[i]["data"]);
        }
      });
  });

  $(".vread table button").click(function(e){
    var button = $(e.target);
    var index = Number(button.attr("name"));
    // console.log(index);
    $.ajax({
      url:'/serialVRead',
      method:'POST',
      data:JSON.stringify({pins:[index]}),
      contentType: 'application/json'
      })
      .done(function(str){
        appendToCmdHistory(str);
        $(".vread-value").eq(index).text(str[0]["data"]);
    });
  });

  $("#verbose-checkbox").click(function(){
    var value = $("#verbose-checkbox").is(":checked")
    $.post("/serialVerbose", {value:value}).done(function(str){
      appendToCmdHistory(str);
    });
  });

  function getVSetEquivalent(X, Y){
    var right = Number($(".grid-opts input[name=right]").val());
    var top = Number($(".grid-opts input[name=top]").val());
    var left = Number($(".grid-opts input[name=left]").val());
    var bottom = Number($(".grid-opts input[name=bottom]").val());

    // TODO: test if the values from the text boxes are valid

    var pins = [right, top, left, bottom];
    var values = [0, 0, 0, 0];

    var convert = function(x) {return Math.abs(Math.round(x/100*255));};
    var x = convert(X);
    var y = convert(Y);
    // console.log('X: ' + X + ', Y: ' + Y);
    if(X >= 0) values[0] = x; else values[2] = x;
    if(Y >= 0) values[1] = y; else values[3] = y;

    return [pins, values];
  }

  $("#cuadricula").click(function(e){
    var offset = $(this).offset();
    var size = $(this).width(); //in pixels
    var settling = $(".grid-opts input[name=settling]").val();
    var resolution = $(".grid-opts input[name=resolution]").val();
    var X = Math.round((e.pageX - offset.left)/size/resolution*200)*resolution - 100;
    var Y = 100 - Math.round((e.pageY - offset.top)/size/resolution*200)*resolution;
    $(".grid-opts input[name=x]").val(X);
    $(".grid-opts input[name=y]").val(Y);

    // console.log('X: ' + X + ', Y: ' + Y);

    var value = $("#autosend-checkbox").is(":checked");
    if(value == true) {

      data = getVSetEquivalent(X, Y);
      var pins = data[0];
      var values = data[1];

      // console.log('pins: ' + pins + ', values: ' + values + ', settling: ' + settling + ', resolution: ' + resolution);

      $.ajax({
        url:'/serialVSet',
        method:'POST',
        data:JSON.stringify({pins:pins,values:values,settling:settling}),
        contentType: 'application/json'
        })
        .done(function(str){
          appendToCmdHistory(str);
      });
    }

  });

  $(".grid-opts button[name=send]").click(function(){
    var X = $(".grid-opts input[name=x]").val();
    var Y = $(".grid-opts input[name=y]").val();
    var settling = $(".grid-opts input[name=settling]").val();

    data = getVSetEquivalent(X, Y);
    var pins = data[0];
    var values = data[1];

    // console.log('pins: ' + pins + ', values: ' + values + ', settling: ' + settling);

    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:JSON.stringify({pins:pins,values:values,settling:settling}),
      contentType: 'application/json'
      })
      .done(function(str){
        appendToCmdHistory(str);
    });
  });

  $(".grid-opts button[name=reset]").click(function(){
    $(".grid-opts input[name=x]").val(0);
    $(".grid-opts input[name=y]").val(0);

    var settling = $(".grid-opts input[name=settling]").val();
    var right = $(".grid-opts input[name=right]").val();
    var top = $(".grid-opts input[name=top]").val();
    var left = $(".grid-opts input[name=left]").val();
    var bottom = $(".grid-opts input[name=bottom]").val();

    var pins = [right, top, left, bottom];
    var values = [0, 0, 0, 0];

    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:JSON.stringify({pins:pins,values:values,settling:settling}),
      contentType: 'application/json'
      })
      .done(function(str){
        appendToCmdHistory(str);
    });
  });

});
