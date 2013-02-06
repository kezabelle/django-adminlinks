;(function($, document, undefined) {
    var $to_iframe = $('.admin-add, .admin-edit, .admin-delete, .admin-history');
    var $doc = $(document);
    var on_popup_close = function(event, action, data) {
        if (typeof action !== 'undefined') {
            window.location.reload(true);
        }
    }
    $doc.bind('fancyiframe-close', on_popup_close);

    $to_iframe.fancyiframe({
        callbacks: {
            href: function($el) {
                var href = $el.attr('href');
                var parts = href.split('?', 2);
                var link = parts[0];
                var qs = (parts[1] || '') + '&_popup=1&_frontend_editing=1';
                return link + '?' + qs;
            }
        },
        elements: {
            prefix: 'django-adminlinks',
            classes: 'adminlinks'
        },
        fades: {
            opacity: 0.85,
            overlayIn: 100,
            overlayOut: 250,
            wrapperIn: 0,
            wrapperOut: 250
        }
    });
})(typeof django !== 'undefined' && django.jQuery || window.jQuery, document);
