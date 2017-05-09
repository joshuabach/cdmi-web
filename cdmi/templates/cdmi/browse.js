/*
 * cdmi/browse
 */

// See: http://stackoverflow.com/questions/29855098/is-there-a-built-in-javascript-function-similar-to-os-path-join/29855282#29855282
function pathJoin(components) {
    return components.join('/').replace(new RegExp('/{1,}', 'g'), '/');
}

$.fn.changeqos = function(target_capability) {
    return this.each(function() {
        var entry = $(this);

        var select = $("#select-" + entry.attr('data-id'));
        var progress = $("#progress-" + entry.attr('data-id'));
        var target = $("#target-" + entry.attr('data-id'));

        var file_path = pathJoin(["{{ view.path }}", entry.attr('data-name')]);
        var type = entry.attr('data-type');

        // Switch to displaying the loading animation
        select.css('display', 'none');
        progress.css('display', 'block');
        target.css('display', 'block');
        select.children('ul[class=dropdown-menu]').empty();

        target.getqosentry(target_capability);

        // Put the container / dataobject in transition
        $.post(pathJoin(["{% url 'cdmi:update' view.site.id '' %}", file_path]), {qos: target_capability, type: type}, function(data) {
            if ('metadata' in data && 'cdmi_recommended_polling_interval' in data.metadata) {
                var next_timeout = data.metadata.cdmi_recommended_polling_interval;
                message('info', "Put "+file_path+" in transition. Polling in "+next_timeout+"ms");

                entry.poll(target_capability, next_timeout);
            } else {
                message('info', "Put "+file_path+" in transition");

                entry.poll(target_capability)
            }
        });
    });
};


$.fn.poll = function(target_capability, timeout) {
    return this.each(function() {
        var entry = $(this);

        var select = $("#select-" + entry.attr('data-id'));
        var progress = $("#progress-" + entry.attr('data-id'));
        var target = $("#target-" + entry.attr('data-id'));
        var qos = $("#qos-" + entry.attr('data-id'));

        // Make sure we are displaying the loading animation
        select.css('display', 'none');
        progress.css('display', 'block');
        target.css('display', 'block');
        select.children('ul[class=dropdown-menu]').empty();

        setTimeout(function() {
            var url = pathJoin(["{% url 'cdmi:object_info' view.site.id view.path %}", entry.attr('data-name')])
            var file_path = pathJoin(["{{ view.path }}", entry.attr('data-name')]);

            // Check if the container / dataobject is still in transition
            $.get(url, function(data) {
                if ('cdmi_recommended_polling_interval' in data.metadata) {
                    var next_timeout = data.metadata.cdmi_recommended_polling_interval;
                    message('info', "Polled "+file_path+", still in transition. Polling again in "+next_timeout+"ms") ;

                    entry.poll(target_capability, next_timeout);
                } else {
                    var new_capability = data.capabilitiesURI.split('/').pop();
                    if (target_capability != data.capabilitiesURI) {
                        message('warning', "Polled "+file_path+", transition finished, but capability is still "+data.capabilitiesURI.split('/').pop());
                    } else {
                        message('info', "Polled "+file_path+", transition to "+new_capability+" finished");

                        // Use the old target qos as the new current qos
                        qos.empty();
                        qos.append(target.contents());
                    }

                    // Switch back to displaying the target capability selection
                    progress.css('display', 'none');
                    target.css('display', 'none');
                    select.css('display', 'block');

                    var capabilities_allowed = data.metadata.cdmi_capabilities_allowed_provided;
                    // Update the list of allowed transitions in the "select" dropdown menu
                    if (capabilities_allowed.length > 0) {
                        capabilities_allowed.forEach(function(target_capability) {
                            select.children('ul[class=dropdown-menu]').append(
                                $('<li>').append(
                                    $('<button>').attr('class', 'btn btn-link')
                                        .click(function() {
                                            entry.changeqos(target_capability);
                                        }).append(
                                            target_capability.split('/').pop()
                                        )
                                )
                            )
                        });
                    } else {
                        select.children('[class=dropdown-toggle]').css('cursor', 'not-allowed');
                        select.children('[class=dropdown-toggle]').css('text-decoration', 'none');
                        select.children('[class=dropdown-toggle]').addClass('disabled');
                        select.children('[class=dropdown-toggle]').attr('title', 'No transitions available for ' + new_capability);
                    }
                }
            });
        }, timeout)
    })
};

var qosid = 0;
$.fn.makeqosentry = function(capabilities_uri, metadata) {
    return this.each(function() {
        var id = qosid++
        $(this).empty();
        $(this).append($('<a>')
                       .css('cursor', 'pointer')
                       .attr('data-toggle', 'collapse')
                       .attr('data-target', '#' + id)
                       .attr('aria-expanded', 'false')
                       .attr('aria-controls', '#' + id)
                       .append(capabilities_uri.split('/').pop()))
            .append($('<div>')
                    .attr('class', 'collapse')
                    .attr('id', id)
                    .append(
                        $('<table>').attr('class', 'table table-bordered')
                            .css('width', 'auto')
                            .append($('<tbody>')
                                    .append(function() {
                                        if ('cdmi_data_storage_lifetime' in metadata) {
                                            return $('<tr>')
                                                .append($('<td>').text('Data lifetime'))
                                                .append($('<td>').text(moment.duration(
                                                    metadata.cdmi_data_storage_lifetime).humanize()))
                                        }
                                    })
                                    .append($('<tr>')
                                            .append($('<td>').text('QoS lifetime'))
                                            .append($('<td>').text(moment.duration(
                                                metadata.cdmi_capability_lifetime).humanize())))
                                    .append($('<tr>')
                                            .append($('<td>').text('Lifetime action'))
                                            .append($('<td>').text(metadata.cdmi_capability_lifetime_action)))
                                    .append($('<tr>')
                                            .append($('<td>').text('Latency'))
                                            .append($('<td>').text(metadata.cdmi_latency)))
                                    .append($('<tr>')
                                            .append($('<td>').text('Throughput'))
                                            .append($('<td>').text(metadata.cdmi_throughput)))
                                    .append($('<tr>')
                                            .append($('<td>').text('Redundancy'))
                                            .append($('<td>').text(metadata.cdmi_data_redundancy)))
                                    .append($('<tr>')
                                            .append($('<td>').text('Geolocation'))
                                            .append($('<td>').text(metadata.cdmi_geographic_placement))))))
    })
}

$.fn.getqosentry = function(capabilities_uri) {
    return this.each(function() {
        var target = $(this);

        // We'll display just the name of the capability until we get the details
        target.text(capabilities_uri.split('/').pop());

        // Retrieve details about the target capability
        $.get(pathJoin(["{% url 'cdmi:object_info' view.site.id '' %}", capabilities_uri]), function(data) {

            // Create a menuentry about the target qos in the table
            target.makeqosentry(capabilities_uri,
                                data.metadata);
        });
    })
}
