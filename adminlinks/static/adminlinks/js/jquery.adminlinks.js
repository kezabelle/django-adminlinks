(function($window, $document, $) {
    $.adminlinks = function(options) {
        $window.__data_changed__ = false;
        $($document).ready(function() {
            var final_options = $.extend(true, {}, $.adminlinks.defaults, options);

            var $close = $('<div />').attr(final_options.close.attributes).html(final_options.close.html);
            var $overlay = $('<div />').attr(final_options.overlay.attributes);
            var $iframe = $('<iframe />').attr(final_options.iframe.attributes);
            var $body = $($document.body);
            var $doc = $($document);
            $overlay.append($close);

            var preventDefault = function(event) {
                event.preventDefault();
                return true;
            };

            var show = function (event) {
                event.preventDefault();
                event.stopPropagation();

                var $element = $(this);
                var target = $element.data('adminlinks-url');
                $iframe.attr('src', target).height(0);
                $body.append($overlay);
                $overlay.after($iframe);
                $overlay.on('click', hide);
                $overlay.show();
                $doc.bind('mousewheel.adminlinks DOMMouseScroll.adminlinks', preventDefault);

                $body.addClass('adminlinks-iframe-loading');
                $iframe.load(function (evt) {
                    $body.removeClass('adminlinks-iframe-loading')
                         .addClass('adminlinks-iframe-open');
                    $doc.trigger('adminlinks-resize');
                    $iframe.show();
                    // if possible, search the iframe's current querystring for
                    // a special variable, and broadcast that to the DOM & parent DOM
                    if ($iframe.contents()[0].location.search.indexOf('_data_changed') !== -1) {
                        $window.__data_changed__ = true;
                        if ($window.frameElement !== void(0) && $window.frameElement !== null) {
                            parent.window.__data_changed__ = true;
                        }
                    }

                });
            };
            var resize = function (event, extra_height) {
                //var old_height = $iframe.height();
                var new_height = $iframe.contents().find("html").height();
                if (extra_height !== void(0) && extra_height !== null) {
                    new_height += parseInt(extra_height);
                }
                //var speed = 0;
                //if (new_height > old_height) {
                //    speed = 0;
                //}
                //$iframe.animate({height: new_height}, 0);
                $iframe.height(new_height);
            };
            $doc.bind('adminlinks-resize', resize);

            var hide = function (event) {
                event.preventDefault();
                event.stopPropagation();
                $doc.off('mousewheel.adminlinks DOMMouseScroll.adminlinks');
                $overlay.off('click');
                $body.removeClass('adminlinks-iframe-open');
                $iframe.remove();
                // we remove after a delay to get nice CSS GPU animation finished.
                setTimeout(function() {
                    $overlay.remove();
                }, 400);
            };
            $doc.on('adminlinks-close', hide);
            $doc.on('click', '[data-adminlinks-url]', show);
        });
        return this;
    };
    $.adminlinks.defaults = {
        'overlay': {
            'attributes': {
                'id': 'adminlinks-overlay'
            }
        },
        'iframe': {
            'attributes': {
                'frameborder': 0,
                'id': 'adminlinks-iframe',
                'allowtransparency': 'true'
            }
        },
        'close': {
            'attributes': {
                'id': 'adminlinks-close',
                'title': 'Close'
            },
            'html': '&times;'
        }
    };
})(window, document, jQuery);
