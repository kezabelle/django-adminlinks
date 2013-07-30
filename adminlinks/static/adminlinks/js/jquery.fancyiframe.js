;(function($, document, undefined) {
    // TODO: maybe refactor like http://ryanflorence.com/authoring-jquery-plugins-with-object-oriented-javascript/
    //var body, doc, overlay, wrapper, content, close;
    var seen_elements = [];
    $.fn.fancyiframe = function(custom_options) {

        // Deep copy of the default options, merged with any custom ones set.
        // Note that we need it to be a deep copy, so we can maintain the default
        // callbacks etc if none are provided, because it's a nested data structure.
        var options = $.extend(true, {}, $.fn.fancyiframe.defaults, custom_options || {});

        if (window.console && window.console.log && options.debug === true) {
            var debug = function() {
                for (var i = 0, args = arguments.length; i < args; i++) {
                    window.console.log(arguments[i]);
                }
            };
        } else {
            var debug = function() { return; };
        }
        debug(options);
        var body = $(document.body);
        var doc = $(document);

        var overlay = $('<div id="django-fancyiframe-overlay"></div>');
        var close = $('<div id="django-fancyiframe-close"></div>');
        body.append(overlay, close);
        overlay.hide() && close.hide();

        var hide = function(event) {
            //debug(event);
            $iframe = $('#django-fancyiframe').remove();
            /* Listen for clicks, or escapes, and close if appropriate */
            overlay.fadeOut(options.fades.overlayOut);
            close.fadeOut(options.fades.overlayOut);

            doc.unbind('mousewheel.fancyiframe DOMMouseScroll.fancyiframe');
            close.unbind('click');
            overlay.unbind('click');
            body.removeClass('django-fancyiframe-open');
        };

        doc.bind('fancyiframe-close', hide);

        var show = function(event) {
            event.preventDefault();
            var $el = $(this);
            var target = options.callbacks.href($el);
            if (target === void(0) || target === '' || target === '#') {
                return;
            }
            close.html(options.callbacks.closeText($el).toString());
            close.attr('title', options.callbacks.closeTitle($el).toString());
            overlay.fadeTo(options.fades.overlayIn, options.fades.opacity);
            overlay.addClass('django-fancyiframe-overlay--working');
            var iframe = $('<iframe src="' + target + '" name="' + name + '" frameborder="0" id="django-fancyiframe">');
            iframe.hide();
            iframe.insertAfter(overlay);
            iframe.load(function(evt) {
                overlay.removeClass('django-fancyiframe-overlay--working');
                iframe.height(iframe.contents().find("html").height());
                iframe.show() && close.show();
                if (window.Modernizer !== void(0) && window.Modernizr.csstransitions !== null && window.Modernizr.csstransitions == true) {
                    iframe.css({
                        'top': 0,
                        '-webkit-transition': 'All 0.5s linear',
                        '-moz-transition': 'All 0.5s linear',
                        '-o-transition': 'All 0.5s linear',
                        'transition': 'All 0.5s linear'
                    });
                } else {
                    iframe.animate({top: 0}, 400);
                }
            });

            // Note: Once upon a time, I tried using delegate() and bind() on specific
            // elements I already had access to (close, overlay, etc), but this doesn't
            // work, because triggering namespaced events ('click.fancyiframe-close',
            // for example) doesn't work unless you know the selector of items it was
            // applied to. No way can you do $.event.trigger('click.fancyiframe-close')
            // or $(document).trigger('click.fancyiframe-close');


            doc.bind('mousewheel.fancyiframe DOMMouseScroll.fancyiframe', function(event) {
                event.preventDefault();
            });
            close.bind('click', function(event) {
                doc.trigger('fancyiframe-close');
            });
            overlay.bind('click', function(event) {
                doc.trigger('fancyiframe-close');
            });
            body.addClass('django-fancyiframe-open');
        };

        var supports_transitions = [
            "transition",
            "WebkitTransition",
            "MozTransition",
            "OTransition",
            "msTransition"
        ];

        return this.each(function(index, value) {
            $(value).bind('click.fancyiframe-open', show);
        });
    };

    $.fn.fancyiframe.defaults = {
        debug: false,
        fades: {
            opacity: 0.85,
            overlayIn: 100,
            overlayOut: 400
        },
        callbacks: {
            href: function($element) {
                //return $element.attr('href') || $element.data('href') || $element.attr('rel');
                return $element.attr('href');
            },
            closeTitle: function($el) {
                return 'Close';
            },
            closeText: function($el) {
                return '&times;';
            },
            contentName: function($element, target) {
                return 'fancy-' + new Date().getTime();
            }
        } // end of callbacks
    } // end of defaults
})(typeof django !== 'undefined' && django.jQuery || window.jQuery, document);
