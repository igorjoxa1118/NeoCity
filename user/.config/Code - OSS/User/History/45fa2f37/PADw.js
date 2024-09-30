$(document).ready(function () {
    $("#all_images").on("click" , function (event) {
  var ready = 0
        $(event.target).parent().css("text-align", "center");
        $(event.target).animate ({
            width: $(event.target).width() * 5,
            height: $(event.target).height() * 5,
        } , 3000);
  var ready = 1
  if (ready == 1) {
    $('body').css("background", "#616161")
  }
    });
});