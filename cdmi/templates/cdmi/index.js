/*
 * cdmi/index
 */

$(document).ready(function() {
    // Hide all other details when one is shown
    var $allDetails = $('#details');
    $allDetails.on('show.bs.collapse','.collapse', function() {
        $allDetails.find('.collapse.in').collapse('hide');
    });

    // Clickable rows
    $("tr.clickable").click(function() {
        window.location = $(this).data("href");
    });
});
