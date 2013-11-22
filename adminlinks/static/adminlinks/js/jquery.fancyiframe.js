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
            var $iframe = $('#django-fancyiframe');
            var distance = 0 - $iframe.height();
            $iframe.remove();
            overlay.fadeOut(options.fades.overlayOut);
            close.fadeOut(options.fades.overlayOut);
            /* Listen for clicks, or escapes, and close if appropriate */
            doc.unbind('mousewheel.fancyiframe DOMMouseScroll.fancyiframe');
            close.unbind('click');
            overlay.unbind('click');
            body.removeClass('django-fancyiframe-open');
        };

        doc.bind('fancyiframe-close', hide);

        var resize = function(event, extra_height) {
            var iframe = $('#django-fancyiframe');
            var old_height = iframe.height();
            var new_height = iframe.contents().find("html").height();
            if (extra_height !== void(0) && extra_height !== null) {
                new_height += parseInt(extra_height);
            }
            var speed = 0;
            if (new_height > old_height) {
                speed = 0;
            }
            iframe.animate({ height: new_height }, speed);
        };
        doc.bind('fancyiframe-resize', resize);

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
            var iframe = $('<iframe src="' + target + '" frameborder="0" id="django-fancyiframe">');
            iframe.hide();
            iframe.insertAfter(overlay);

            // we can't use iframe.ready() because
            //  * We only get one ready() event - when it's first run, no
            //    subsequent page-loads fire it. Annoying, as it means we cannot
            //    track the _data_changed event sooner
            //  * We need to change/fix the height of the iframe each time,
            //    and the ready() event is *TOO* soon for that.
            iframe.load(function(evt) {
                overlay.removeClass('django-fancyiframe-overlay--working');
                // if possible, search the iframe's current querystring for
                // a special variable, and broadcast that to the DOM & parent DOM
                if (iframe.contents()[0].location.search.indexOf('_data_changed') !== -1) {
                    window.__data_changed__ = true;
                    if (window.frameElement !== void(0) && window.frameElement !== null) {
                        parent.window.__data_changed__ = true;
                    }
                }
                // set the height
                iframe.show() && close.show();
                doc.trigger('fancyiframe-resize');
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
                var href = $element.attr('href');
                var adminlinks_action = $element.data('adminlinks') || $element.attr('data-adminlinks');
                if (adminlinks_action === void(0) || adminlinks_action === '') {
                    return href;
                }
                if (adminlinks_action.toString() === 'autoclose') {
                    if (href.indexOf('?') > -1) {
                        href += '&_autoclose=1';
                    } else {
                        href += '?_autoclose=1';
                    }
                    return href;
                }
                // none of the previous if branches caught
                return href;
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
