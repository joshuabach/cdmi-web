/*
 * cdmi/browse
 */


$.fn.changeqos = function(target_capability) {
    return this.each(function() {
        var entry = $(this);
        var target = $("#target-" + entry.attr('data-id'));

        var file_path = "{{ path }}/" + entry.attr('data-name');
        var type = entry.attr('data-type');

        $.get("{% url 'cdmi:object_info' site.id '' %}" + target_capability, function(data) {
            var target_capability_metadata = data.metadata;

            $('#changeqos-file-name').text(file_path)
            $('#changeqos-object-name').text(target_capability.split('/').pop())
            $('#changeqos-object-latency').text(target_capability_metadata.cdmi_latency)
            $('#changeqos-object-copies').text(target_capability_metadata.cdmi_data_redundancy)
            $('#changeqos-object-location').text(target_capability_metadata.cdmi_geographic_placement)
            $('#changeqos-object-transitions').text(target_capability_metadata.cdmi_capabilities_allowed)

            $('#changeqos-button').off()
            $('#changeqos-button').click(function() {
                $.post("{% url 'cdmi:update' site.id '' %}" + file_path,
                       {qos: target_capability, type: type},
                       function(data) {
                           target.makeqosentry(target_capability,
                                               target_capability_metadata);
                           entry.poll();
                       })
            });

            $('#changeqos').modal('show');
        });
    })
};


$.fn.poll = function(timeout) {
    return this.each(function() {
        var entry = $(this);

        var select = $("#select-" + entry.attr('data-id'));
        var progress = $("#progress-" + entry.attr('data-id'));
        var target = $("#target-" + entry.attr('data-id'));
        var qos = $("#qos-" + entry.attr('data-id'));

        select.css('display', 'none');
        progress.css('display', 'block');
        target.css('display', 'block');
        select.children('ul[class=dropdown-menu]').empty();

        setTimeout(function() {
            var url = "{% url 'cdmi:object_info' site.id path %}" + entry.attr('data-name');

            $.get(url, function(data) {
                if ('cdmi_recommended_polling_interval' in data.metadata) {
                    var next_timeout = data.metadata.cdmi_recommended_polling_interval;
                    console.log("Polled %o, still in transition. Sleeping %o", url, next_timeout) ;
                    entry.poll(next_timeout);
                } else {
                    console.log("Polled %o, transition finished", url) ;
                    progress.css('display', 'none');
                    target.css('display', 'none');
                    select.css('display', 'block');

                    var new_capability = data.capabilitiesURI.split('/').pop();
                    qos.empty();
                    qos.append(target.contents());

                    // now we have to update the possible target capabilities
                    var capabilities_allowed = data.metadata.cdmi_capabilities_allowed_provided;
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
