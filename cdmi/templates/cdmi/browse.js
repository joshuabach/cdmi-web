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

            $('#changeqos-file-name')[0].innerHTML = file_path;
            $('#changeqos-object-name')[0].innerHTML = target_capability.split('/').pop();
            $('#changeqos-object-latency')[0].innerHTML = target_capability_metadata.cdmi_latency;
            $('#changeqos-object-copies')[0].innerHTML = target_capability_metadata.cdmi_data_redundancy;
            $('#changeqos-object-location')[0].innerHTML = target_capability_metadata.cdmi_geographic_placement;
            $('#changeqos-object-transitions')[0].innerHTML = target_capability_metadata.cdmi_capabilities_allowed;

            $('#changeqos-button').off()
            $('#changeqos-button').click(function() {
                $.post("{% url 'cdmi:update' site.id '' %}" + file_path,
                       {qos: target_capability, type: type},
                       function(data) {
                           target[0].innerHTML = target_capability.split('/').pop();
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
                    qos[0].innerHTML = new_capability;

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
