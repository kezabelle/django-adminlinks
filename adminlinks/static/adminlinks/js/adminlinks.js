;(function($, document, undefined) {
    var $to_iframe = $('.admin-add, .admin-edit, .admin-delete, .admin-history, .admin-toolbar-link');
    var $doc = $(document);
    var $body = $('body', $doc).eq(0);
    var on_popup_close = function(event, action, data) {
        if (typeof action !== 'undefined') {
            window.location.reload(true);
        }
    }
    $doc.bind('fancyiframe-close', on_popup_close);

    var toggle_editing = function(event) {
        event.preventDefault();
        var $me = $(this);
        $me.toggleClass('icon-cog-circled')
            .toggleClass('icon-lock-circled');
        $body.toggleClass('admin-editing');
    }
    $('.admin-toolbar-toggle .icon-cog-circled').bind('click', toggle_editing);

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
