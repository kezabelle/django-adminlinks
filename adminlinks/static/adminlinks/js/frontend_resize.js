(function($p, $) {
    $(document).ready(function() {
        var newheight = $(document).height();
        $p.event.trigger('frontend_editor_loaded', newheight);
    });
})(parent.django.jQuery, django.jQuery);
