(function($window, $document, $) {
    // $ is {{ js_namespace }}
    var noop = function() {};
    var $console = $window.console || {};
    var $log = $console.log || noop;

    if ($ === void(0)) {
        return $log.call($console, "jQuery not found");
    } else {
        /* {% load static %} */

        var load_css = function($, $log, $console) {
            // include_css is {{ include_css }}
            /*{% if include_css %}*/
            var link_tag = $("link[href='{% static 'adminlinks/css/toolbar.css' %}']");
            if (link_tag.length > 0) {
                $log.call($console, "adminlinks CSS for `{{ admin_site }}` already on the page");
                return false;
            } else {
                $log.call($console, "adminlinks CSS for `{{ admin_site }}` has been added to the head");
                $("head").append('<link href="{% static 'adminlinks/css/toolbar.css' %}" rel="stylesheet">');
                return true;
            }
            /* {% else %}*/
            return true;
            /*{% endif %}*/
        };

        var load_html = function($, $log, $console) {
            // include_html is {{ include_html }}
            /*{% if include_html %}*/
            var adminlinks_id = "#adminlinks-for-{{ admin_site }}";
            var found_already = $(adminlinks_id);
            if (found_already.length > 0) {
                $log.call($console, "adminlinks for `{{ admin_site }}` already on the page");
                return false;
            } else {
                $log.call($console, "adminlinks for `{{ admin_site }}` have been embedded");
                $("body").append("{{ json|safe }}");
                return true;
            }
            /* {% else %}*/
            return true;
            /*{% endif %}*/
        };

        var build_fragment = function() {
            var $this = $(this);
            var json_data = $this.data('adminlinks-{{ admin_site }}');
            var link_data;
            var output = '';
            if (json_data.length === 0) {
                return false;
            }
            for(var linkable in json_data) {
                if (json_data.hasOwnProperty(linkable)) {
                    link_data = json_data[linkable];
                    output += '<a href="' + link_data.url + '" data-adminlinks-url="' + link_data.url + '" class="">' + link_data.title + '</a>';
                }
            }
            if (output.length >= 0) {
                output = '<span class="">' + output + '</span>';
                $this.append(output);
                return true;
            } else {
                return false;
            }

        };

        var load_fragments = function($, $log, $console) {
            var found = $('[data-adminlinks-{{ admin_site }}]');
            if (found.length === 0) {
                $log.call($console, "no `data-adminlinks` for `{{ admin_site }}` on the page");
                return false;
            } else {
                $log.call($console, "found " + found.length.toString() + " `data-adminlinks` for `{{ admin_site }}` on the page");
                // avoiding found.each() cos this is much faster.
                for (var i = 0, len = found.length; i < len; i++) {
                    build_fragment.call(found[i]);
                }
                return true;
            }
        };

        var on_ready = function() {
            var admin_site = "{{ admin_site }}";
            return load_html.call(this, $, $log, $console) &&
                   load_css.call(this, $, $log, $console) &&
                   load_fragments.call(this, $, $log, $console);

        };
        return $($document).ready(on_ready);
    };
})(window, document, {{ js_namespace }} || void(0));
