;(function($, document, undefined) {
    // this dude is super important, because it reflects to the page that something
    // from one of the child windows has decided the page needs changing.
    // when we close the popup, we check it to decide whether to reload.
    window.__data_changed__ = false;

    var $to_iframe = $('.admin-add, .admin-edit, .admin-delete, .admin-history, .admin-toolbar-link');
    var $doc = $(document);
    var $body = $('body', $doc).eq(0);
    var on_popup_close = function(event, action, data) {
        if (window.__data_changed__ === true) {
            window.location.reload();
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

    if (window.frameElement === null) {
        $to_iframe.fancyiframe({
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
    }
})(typeof django !== 'undefined' && django.jQuery || window.jQuery, document);
