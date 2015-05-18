(function($window, $document, $) {

    var noop = function() {};
    var $console = $window.console || {};
    var $log = $console.log || noop;

    if ($ === void(0)) {
        return $log.call($console, "jQuery not found");
    } else {
        /* {% load static %} */

        var load_css = function($, $log, $console) {
            var link_tag = $("link[href='{% static 'adminlinks/css/toolbar.css' %}']");
            if (link_tag.length > 0) {
                $log.call($console, "adminlinks CSS for `{{ admin_site }}` already on the page");
                return false;
            } else {
                $log.call($console, "adminlinks CSS for `{{ admin_site }}` has been added to the head");
                $("head").append('<link href="{% static 'adminlinks/css/toolbar.css' %}" rel="stylesheet">');
                return true;
            }
        };

        var load_html = function($, $log, $console) {
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
        };

        var on_ready = function() {
            var admin_site = "{{ admin_site }}";
            return load_html.call(this, $, $log, $console) && load_css.call(this, $, $log, $console);
        };
        return $($document).ready(on_ready);
    };
})(window, document, {{ js_namespace }} || void(0));
