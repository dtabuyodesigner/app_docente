/**
 * Dark Mode Toggle — APP_EVALUAR
 * Persiste la preferencia en localStorage
 * Detecta preferencia del sistema si no hay preferencia guardada
 */
(function () {
    const HTML = document.documentElement;
    const STORAGE_KEY = 'app_evaluar_theme';

    // Función para aplicar el tema
    function applyTheme(theme) {
        HTML.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        // Actualizar meta theme-color para móviles
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.content = theme === 'dark' ? '#121220' : '#003366';
        }
    }

    // Determinar tema inicial
    function getInitialTheme() {
        // 1. Preferencia guardada
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === 'dark' || stored === 'light') return stored;
        // 2. Preferencia del sistema operativo
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
        return 'light';
    }

    // Aplicar tema al cargar
    applyTheme(getInitialTheme());

    // Escuchar cambios en preferencia del sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });

    // Función global para toggle (llamada desde HTML)
    window.toggleDarkMode = function () {
        const current = HTML.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    };

    // Exponer función para obtener tema actual
    window.getCurrentTheme = function () {
        return HTML.getAttribute('data-theme') || 'light';
    };
})();
