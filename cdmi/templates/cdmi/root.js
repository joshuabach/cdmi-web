/*
 * cdmi/root
 */

$(document).ready(function() {
    var $loading = $('#loadingDiv').hide();
    $(document)
        .ajaxStart(function () {
            $loading.show();
        })
        .ajaxStop(function () {
            $loading.hide();
        });
});

function message(lvl, msg) {
    console.log(msg);

    $('#messages > tbody:last-child')
        .append($('<tr>').attr('class', lvl)
                .append($('<td>').text(msg)));
}

function clear_messages() {
    $('#messages > tbody').empty();
}

