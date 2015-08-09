// Console-polyfill. MIT license.
// https://github.com/paulmillr/console-polyfill
// Make it safe to do console.log() always.
;(function(global) {
  'use strict';
  global.console = global.console || {};
  var con = global.console;
  var prop, method;
  var empty = {};
  var dummy = function() {};
  var properties = 'memory'.split(',');
  var methods = ('assert,clear,count,debug,dir,dirxml,error,exception,group,' +
     'groupCollapsed,groupEnd,info,log,markTimeline,profile,profiles,profileEnd,' +
     'show,table,time,timeEnd,timeline,timelineEnd,timeStamp,trace,warn').split(',');
  while (prop = properties.pop()) if (!con[prop]) con[prop] = empty;
  while (method = methods.pop()) if (!con[method]) con[method] = dummy;
})(window);

//noinspection BadExpressionStatementJS
(function($window, $document, $jsnamespace) {
    // {% load i18n static %}
    var configuration = {
        'is_authenticated': {{ configuration.is_authenticated }},
        'include_toolbar_css': {{ configuration.include_css }},
        'include_toolbar_html': {{ configuration.include_html }},
    };
    var $ = $window[$jsnamespace];

    if ($ === void(0)) {
        return console.debug("jQuery not found");
    }

    if (configuration.is_authenticated === 0) {
        return console.log("Anonymous users cannot use the admin");
    }

    var load_css = function($, conf) {
        if (conf.include_toolbar_css === 0) {
            return false;
        }
        var link_tag = $document.querySelectorAll("link[href='{% static 'adminlinks/css/toolbar.css' %}']");
        if (link_tag.length > 0) {
             console.debug("adminlinks CSS [{% static 'adminlinks/css/toolbar.css' %}] for `{{ admin_site }}` already on the page");
            return false;
        } else {
            $("head").append('<link href="{% static 'adminlinks/css/toolbar.css' %}" rel="stylesheet">');
             console.debug("adminlinks CSS [{% static 'adminlinks/css/toolbar.css' %}] for `{{ admin_site }}` has been added to the head");
            return true;
        }
    };

    var load_html = function($, conf) {
        if (conf.include_toolbar_html === 0) {
            return false;
        }
        var adminlinks_id = "#adminlinks-for-{{ admin_site }}";
        var found_already = document.getElementById(adminlinks_id);
        if (found_already !== null) {
             console.debug("adminlinks for `{{ admin_site }}` already on the page");
            return false;
        } else {
             console.debug("adminlinks for `{{ admin_site }}` have been embedded");
            $("body").append("{{ toolbar_html|safe }}");
            return true;
        }
    };

    var build_fragment = function() {
        var $this = $(this);
        var json_data = $this.data('adminlinks-{{ admin_site }}');
        var link_data;
        var output = '';
        if (json_data.length === 0) {
            return false;
        }
        var fragment_html = "{{ fragment_html|safe }}";
        for(var linkable in json_data) {
            if (json_data.hasOwnProperty(linkable)) {
                link_data = json_data[linkable];
                output += fragment_html.replace(/{% verbatim %}{{ url }}{% endverbatim %}/g, link_data.url)
                                       .replace(/{% verbatim %}{{ title }}{% endverbatim %}/g, link_data.title)
                                       .replace(/{% verbatim %}{{ namespace }}{% endverbatim %}/g, '{{ admin_site }}');
            }
        }
        if (output.length >= 0) {
            output = '<aside class="adminlinks-fragment-wrapper adminlinks-fragment-wrapper__{{ admin_site }}">' +
            '<span class="adminlinks-fragment-icon adminlinks-fragment-icon__{{ admin_site }}">&nbsp;</span>' +
            '<ol class="adminlinks-fragment-menu">' + output + '</ol></aside>';
            $this.after(output);
            return true;
        } else {
            return false;
        }

    };

    var load_fragments = function($) {
        var found = $document.querySelectorAll('[data-adminlinks-{{ admin_site }}]');
        if (found.length === 0) {
            console.debug("no `data-adminlinks-{{ admin_site }}` on the page");
            return false;
        } else {
            console.debug("found " + found.length.toString() + " `data-adminlinks-{{ admin_site }}` on the page");
            // avoiding found.each() cos this is much faster.
            for (var i = 0, len = found.length; i < len; i++) {
                build_fragment.call(found[i]);
            }
            return true;
        }
    };

    var on_ready = function() {
        var admin_site = "{{ admin_site }}";
        var loaded_html = load_html.call(this, $, configuration);
        var loaded_css = load_css.call(this, $, configuration);
        var loaded_fragments = load_fragments.call(this, $, configuration);
        return loaded_html && loaded_css && loaded_fragments;

    };
    return $($document).ready(on_ready);
})(window, document, '{{ js_namespace }}');
