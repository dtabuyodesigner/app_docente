/**
 * Debug logging wrapper — solo muestra logs cuando window.DEBUG = true
 *
 * Uso:
 *   <script>window.DEBUG = true;</script>  <!-- solo en desarrollo -->
 *   dbg.log('mensaje');
 *   dbg.warn('advertencia');
 *   dbg.error('error');
 */
var dbg = (function () {
    var DEBUG = typeof window !== 'undefined' && window.DEBUG === true;
    return {
        log: function () { if (DEBUG) console.log.apply(console, arguments); },
        warn: function () { if (DEBUG) console.warn.apply(console, arguments); },
        error: function () { if (DEBUG) console.error.apply(console, arguments); }
    };
})();
