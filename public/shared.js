$(document).ready(function() {
  var flashMessage = function(text, type) {
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
});
