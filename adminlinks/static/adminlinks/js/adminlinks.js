;(function($, document, undefined) {
    // this dude is super important, because it reflects to the page that something
    // from one of the child windows has decided the page needs changing.
    // when we close the popup, we check it to decide whether to reload.
    window.__data_changed__ = false;
    var cookie_key = 'django-adminlinks-state';
    var final_cookie = encodeURIComponent(cookie_key) + '=' + encodeURIComponent(1);

    var on_popup_close = function(event, action, data) {
        if (window.__data_changed__ === true) {
            if (window.Turbolinks !== void(0) &&
                window.Turbolinks.visit !== void(0) &&
                window.Turbolinks.visit !== null) {
                window.Turbolinks.visit(window.location.href);
            } else {
                window.location.reload();
            }
        }
    };

    var toggle_editing = function(event) {
        if ($.inArray('django-adminlinks-state=1', document.cookie.split('; ')) > -1) {
            $(document.body).addClass('django-adminlinks--admin-editing');
        } else {
            $(document.body).removeClass('django-adminlinks--admin-editing');
        }
    };

    var set_toggle_state = function(event) {
        event.preventDefault();
        var now = new Date();
        if ($.inArray(final_cookie, document.cookie.split('; ')) === -1) {
            now.setDate(now.getDate() + 1);
        } else {
            now.setDate(now.getDate() - 365);
        }
        document.cookie = final_cookie + '; expires=' + now.toUTCString();
        return toggle_editing(event);
    };


    var adminlinks_setup = function() {
        if (window.frameElement === null) {
            $('.django-adminlinks--btn').fancyiframe({
                debug: true,
                elements: {
                    prefix: 'django-adminlinks',
                    classes: 'adminlinks'
                },
                fades: {
                    opacity: 0.93,
                    overlayIn: 0,
                    overlayOut: 0
                }
            });
        }
        // this has to be here because of document readiness
        $('.django-adminlinks--toggle').bind('click', set_toggle_state);
        toggle_editing($.Event());
    };
    // hopefully doing what https://github.com/kossnocorp/jquery.turbolinks says
    // so that after a Turbolinks refresh, events work?
    $(document).bind('fancyiframe-close', on_popup_close);
    $(document).ready(adminlinks_setup);
})(typeof django !== 'undefined' && django.jQuery || window.jQuery, document);
