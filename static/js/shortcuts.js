/**
 * Global Keyboard Shortcuts — APP_EVALUAR
 * 
 * Atajos disponibles:
 * - Ctrl+S: Guardar (en formularios con botón .btn-success o [type="submit"])
 * - Ctrl+F: Enfocar buscador (input#searchInput, #search, o similar)
 * - Esc: Cerrar modal activo (ya implementado en navigation.js)
 * - Ctrl+N: Nuevo registro (botón "Nuevo" o "Añadir")
 */
(function () {
    'use strict';

    // Prevenir que los atajos se disparen dentro de inputs/textareas (excepto Ctrl+F)
    function isTyping(e) {
        const tag = e.target.tagName;
        return (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') && e.key !== 'f';
    }

    document.addEventListener('keydown', function (e) {
        // Ignorar si el usuario está escribiendo en un campo
        if (isTyping(e) && !(e.ctrlKey && e.key === 'f')) return;

        // Ctrl+S — Guardar
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            const btn = document.querySelector('.btn-success, .btn-save, .btn-primary, [type="submit"]');
            if (btn && !btn.disabled) {
                btn.click();
            }
        }

        // Ctrl+F — Buscar
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('#searchInput, #search, #filterSearch, input[placeholder*="Buscar"], input[placeholder*="Filtrar"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Ctrl+N — Nuevo
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            const btn = document.querySelector('.btn-new, .btn-add, .btn-crear, [onclick*="nuevo"], [onclick*="Nuevo"], [onclick*="crear"], [onclick*="Añadir"]');
            if (btn && !btn.disabled) {
                btn.click();
            }
        }
    });
})();
