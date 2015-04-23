$(document).ready(function(){

  var connStateText = $("#conn-state-text");
  var commHistMax = 15;
  var scriptHistMax = 10;

  $.get("/isConnected").done(function(value) {
    str = value == 1 ? "Connected" : "Disconnected";
    connStateText.text(str);
  });

  $("#script-history-list li").click(function() {
    $("#script-textbox").val($(this).text());
  });

  function appendToScriptHistory(str) {
    var histlist = $("#script-history-list");
    var item = $("<li>"+str+"</li>").click(function() {
      $("#script-textbox").val($(this).text());
    });
    histlist.append(item);
    var length = histlist.children().length;
    if(length > scriptHistMax) {
      histlist.children().slice(0, length - scriptHistMax).remove();
    }
  }

  function appendToCmdHistory(result, flashtext, cmdtext) {
    var histlist = $("#comm-msg-hist-list");
    var url, obj;
    // TODO: handle data printing??
    if(result['success'] == true) {
      flashMessage(flashtext,'success');
      var item = $("<li>"+cmdtext+"</li>").click(execComHistItem);
      histlist.append(item);
    } else {
      flashMessage(result['info'],'error');
    }
    var length = histlist.children().length;
    if(length > commHistMax) {
      histlist.children().slice(0, length - commHistMax).remove();
    }
  }

  var execComHistItem = function() {
    try {
      obj = JSON.parse($(this).text());
    } catch(err) {
      flashMessage("Invalid syntax", 'error');
      return;
    }
    switch(obj["cmd"]){
      case "vset":
        url = "/serialVSet";
        break;
      case "vread":
        url = "/serialVRead";
        break;
      case "comtest":
        url = "/serialComtest";
        break;
      case "script":
        url = "/serialScript";
        break;
      case "verbose":
        url = "/serialVerbose";
        break;
      default:
        console.log("Unexpected command name");
    }
    $.ajax({
      url:url,
      method:'POST',
      data:JSON.stringify(obj["input"]),
      contentType: 'application/json'
    })
    .done(function(res){
      if(res["success"] == true) {
        flashMessage(obj["cmd"],'success');
      } else {
        flashMessage(res["info"],'error');
      }
    });
  };

  function flashMessage(text, type) {
    noty({
      text:text,
      type:type,
      timeout:2000,
      killer:true,
      dismissQueue:false,
      theme:'relax',
      layout:'topCenter',
      animation:{
        open: {height: 'toggle'},
        close: {height: 'toggle'},
        easing: 'swing',
        speed: 300
      }});
  }
  window.app = {flashMessage: flashMessage};

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
    $.get("/serialComtest").done(function(res){
      appendToCmdHistory(res, 'comtest', '{"cmd":"comtest"}');
    });
  });

  $("button#vset-button").click(function(){
    var text = $(".vset input[name=batch]").val();
    if(text == []){
      return;
    }
    text = text.trim();

    var parts = text.split(',');
    if(!$.isArray(parts)) {
      flashMessage("Invalid expression",'error');
      return;
    }
    if(parts.length != 3) {
      flashMessage("Invalid expression",'error');
      return;
    }
    var pins = parts[0].trim().split(' ').map(Number);
    if(pins.some(function(val){return isNaN(val);})) {
      flashMessage("Invalid expression",'error');
      return;
    }
    if(pins.some(isValidVSetPin)) {
      flashMessage("Invalid pin",'error');
      return;
    }
    var values = parts[1].trim().split(' ').map(Number);
    if(values.some(function(val){return isNaN(val);})) {
      flashMessage("Invalid expression",'error');
      return;
    }
    if(values.some(function(val){return val>255 || val<0})){
      flashMessage("Invalid value",'error');
      return;
    }
    if(values.length != pins.length) {
      flashMessage("Invalid expression",'error');
      return;
    }
    var settling = Number(parts[2]);
    var data = JSON.stringify({pins:pins,values:values,settling:settling});
    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:data,
      contentType: 'application/json'
    })
    .done(function(res){
      appendToCmdHistory(res, 'vset '+pins+' '+values+' '+settling,
        '{"cmd":"vset","input":'+data+'}');
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

    var data = JSON.stringify({pins:[pin],values:[value],settling:settling});
    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:data,
      contentType: 'application/json'
    })
    .done(function(res){
      appendToCmdHistory(res, 'vset '+pin+' '+value+' '+settling,
        '{"cmd":"vset","input":'+data+'}');
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
      flashMessage("Invalid pin",'error');
      return;
    }
    if(pins.some(function(val){return isNaN(val);})) {
      flashMessage("Invalid expression",'error');
      return;
    }
    // this request format is a must for sending json arrays to cherrypy
    var data = JSON.stringify({pins:pins});
    $.ajax({
      url:'/serialVRead',
      method:'POST',
      data:data,
      contentType: 'application/json'
    })
    .done(function(res){
      appendToCmdHistory(res, 'vread '+pins, '{"cmd":"vread","input":'+data+'}');
      lim = Math.min(res["data"]["data"].length, 4);
      for(var i = 0; i < lim; i++) {
        $(".vread-value").eq(pins[i]).text(res["data"]["data"][i]);
      }
    });
  });

  $(".vread table button").click(function(e){
    var button = $(e.target);
    var index = Number(button.attr("name"));
    var data = JSON.stringify({pins:[index]});
    $.ajax({
      url:'/serialVRead',
      method:'POST',
      data:data,
      contentType: 'application/json'
    })
    .done(function(res){
      appendToCmdHistory(res, 'vread '+index,'{"cmd":"vread","input":'+data+'}');
      $(".vread-value").eq(index).text(res["data"]["data"]);
    });
  });

  $("#verbose-checkbox").click(function(){
    var value = $("#verbose-checkbox").is(":checked")
    $.post("/serialVerbose", {value:value}).done(function(res){
      appendToCmdHistory(res, 'verbose '+value,
        '{"cmd":"verbose","input":'+JSON.stringify({value:value})+'}');
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

    var value = $("#autosend-checkbox").is(":checked");
    if(value == true) {

      data = getVSetEquivalent(X, Y);
      var pins = data[0];
      var values = data[1];

      var data = JSON.stringify({pins:pins,values:values,settling:settling});
      $.ajax({
        url:'/serialVSet',
        method:'POST',
        data:data,
        contentType: 'application/json'
      })
      .done(function(res){
        appendToCmdHistory(res, 'vset '+pins+' '+values+' '+settling,
          '{"cmd":"vset","input":'+data+'}');
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

    var data = JSON.stringify({pins:pins,values:values,settling:settling});
    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:data,
      contentType: 'application/json'
    })
    .done(function(res){
      appendToCmdHistory(res, 'vset '+pins+' '+values+' '+settling,
        '{"cmd":"vset","input":'+data+'}');
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

    var data = JSON.stringify({pins:pins,values:values,settling:settling});
    $.ajax({
      url:'/serialVSet',
      method:'POST',
      data:data,
      contentType: 'application/json'
    })
    .done(function(res){
      appendToCmdHistory(res, 'vset '+pins+' '+values+' '+settling,
        '{"cmd":"vset","input":'+data+'}');
    });
  });

  $(".scripts button").click(function() {
    var text = $("#script-textbox").val();
    if(text=="") return;
    try{
      var cmd = JSON.parse(text);
    } catch(err) {
      flashMessage('Invalid syntax','error');
      return;
    }
    $.ajax({
      url:'/serialScript',
      method:'POST',
      data:text,
      contentType: 'application/json'
    })
    .done(function(result){
      appendToCmdHistory(result, cmd['fname'], '{"cmd":"script","input":'+text+'}');
      if(result['success'] == true) {
        appendToScriptHistory(text);
      }
    });
  });

  var modalstate = false;
  $("#calibration-trigger").click(function() {
    if(modalstate == false){
      modalstate = true;
      $("#modal-container").attr("class","modal");
      $("#modal-container").load("/calibration/index");
      // $.get("/calibration/index").done(function(html) {
      //   $("#modal-container").attr("class","modal");
      //   console.log(html);
      //   $("#modal-container").load(html);
      // });
    } else {
      modalstate = false;
      $("#modal-container").removeAttr("class");
      $("#modal-container").empty();
    }
  });
});
