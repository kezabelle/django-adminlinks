var _class_name = 'admin-editable-box';
var $body = $('body').eq(0);
var box = $('<div class="'+_class_name+'"><div class="internal">Edit</div>').appendTo($body);

var $elements = $('[data-editable]');
var elements = $elements.toArray();

var last = +new Date;
$elements.addClass('admin-editable');

$body.mousemove(function(e) {
    var offset, el = e.target;
    var now = +new Date;
    if (now-last < 35)
        return;
    last = now;
    if (el === $body) {
        box.hide();
        return;
    } else if (el.className === _class_name) {
        box.hide();
        el = document.elementFromPoint(e.clientX, e.clientY);
        if (el instanceof HTMLIFrameElement) {
            console.log('erk');
        }
    }
    if ($.inArray(el, elements) > -1) {
        var $el = $(el);
        offset = $el.offset();
        box.css({
            width:  $el.outerWidth()  - 2,
            height: $el.outerHeight() - 2,
            left:   offset.left,
            top:    offset.top
        });
        box.show();
    } else {
        box.hide();
    }
});
