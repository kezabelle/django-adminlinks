(function($window) {
    var noop = function() {};
    var $console = $window.console || {};
    var $log = $console.log || noop;
    $log.call($console, "Anonymous users cannot use the admin");
})(window);
