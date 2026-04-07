/**
 * --- UNIFIED NAVIGATION SYSTEM ---
 * Dynamically generates the navbar for all pages.
 */

const MENU_STRUCTURE = [
    {
        category: "Gestión",
        icon: "📋",
        items: [
            { name: "Alumnos", icon: "👦", url: "/alumnos" },
            { name: "Pasar Lista", icon: "📋", url: "/asistencia" },
            { name: "Horario", icon: "⏰", url: "/horario" },
            { name: "Reuniones", icon: "👨‍👩‍👧‍👦", url: "/reuniones" },
            { name: "Cumpleaños", icon: "🎂", url: "/cumpleanos" }
        ]
    },
    {
        category: "Docencia",
        icon: "🍎",
        items: [
            { name: "Diario", icon: "📓", url: "/diario" },
            { name: "Programación", icon: "📅", url: "/programacion" },
            { name: "Clase de Hoy", icon: "🏫", url: "/static/clase_hoy.html" },
            { name: "Rúbricas", icon: "📝", url: "/rubricas" },
            { name: "Tareas", icon: "✅", url: "/tareas" }
        ]
    },
    {
        category: "Evaluación",
        icon: "📊",
        items: [
            { name: "Evaluación", icon: "📋", url: "/static/evaluacion.html" },
            { name: "Evaluar Todo", icon: "🚀", url: "/static/evaluar_todo.html" },
            { name: "Cuaderno", icon: "📓", url: "/static/cuaderno_evaluacion.html" },
            { name: "Progreso", icon: "📈", url: "/static/progreso_clase.html" },
            { name: "Informes", icon: "📜", url: "/informes" }
        ]
    },
    {
        category: "Recursos",
        icon: "📦",
        items: [
            { name: "Biblioteca", icon: "📚", url: "/biblioteca" },
            { name: "Material", icon: "📦", url: "/material" }
        ]
    }
];

function initNavigation() {
    const header = document.createElement('header');
    header.className = 'nav-wrapper';

    const currentPath = window.location.pathname;

    let menuHtml = `
        <div class="nav-container">
            <a href="/" class="nav-logo">
                <span>📘</span> Inicio
            </a>
            <nav class="nav-menu">
    `;

    MENU_STRUCTURE.forEach(cat => {
        // Check if any item in this category is active
        const isActive = cat.items.some(item => currentPath === item.url || (item.url.includes('.html') && currentPath.endsWith(item.url.split('/').pop())));

        menuHtml += `
            <div class="nav-item">
                <div class="nav-link ${isActive ? 'active' : ''}">
                    ${cat.icon} ${cat.category}
                </div>
                <div class="nav-dropdown">
                    ${cat.items.map(item => `
                        <a href="${item.url}" class="dropdown-link ${currentPath === item.url ? 'active' : ''}">
                            <span class="dropdown-icon">${item.icon}</span>
                            <span>${item.name}</span>
                        </a>
                    `).join('')}
                </div>
            </div>
        `;
    });

    menuHtml += `
            </nav>
            <div class="nav-right">
                <div class="group-selector-container">
                    <span>📚</span>
                    <select id="globalGroupSelect" onchange="changeActiveGroup(this.value)" class="group-selector-select">
                        <option value="">Cargando...</option>
                    </select>
                </div>
                <button class="dark-mode-toggle" onclick="toggleDarkMode()" title="Cambiar modo claro/oscuro">🌙</button>
                <a href="/configuracion" class="nav-link" title="Configuración">⚙️</a>
                <a href="/ayuda" class="nav-link" title="Ayuda">💡</a>
                <a href="/logout" class="nav-link" title="Cerrar Sesión" style="color: #ffb300">🚪</a>
                <a href="javascript:void(0)" onclick="confirmExitApp()" class="nav-link" title="Cerrar Aplicación" style="color: #ff4d4d">✖</a>
            </div>
        </div>
    `;

    header.innerHTML = menuHtml;

    // Insert at the beginning of body
    document.body.prepend(header);

    // If global_groups.js is loaded, trigger the data load
    if (typeof loadGroupSelectorData === 'function') {
        loadGroupSelectorData();
    }

    // Comprobar actualizaciones en segundo plano
    setTimeout(checkAppUpdates, 3000); // Esperar 3s a que cargue la página
    setInterval(checkAppUpdates, 15 * 60 * 1000); // Recheck cada 15 minutos
}

async function checkAppUpdates() {
    try {
        const res = await fetch('/api/admin/check_updates?t=' + Date.now());
        if (!res.ok) return; // No es admin o sin conexión — ignorar silenciosamente
        const data = await res.json();
        if (data.ok && data.update_available) {
            const latestVersion = data.latest_version || "Nueva";
            const omittedVersion = localStorage.getItem('update-omitted-version');
            if (omittedVersion === latestVersion) return;

            // En el panel de control ya hay banner verde; en otras páginas mostramos el rojo
            const enPanel = !!document.getElementById('updateAlert');
            if (!enPanel) showUpdateBanner(latestVersion);
            addUpdateBadgeToConfig();
        }
    } catch (e) {
        // Sin conexión o error — no mostrar nada
    }
}

function showUpdateBanner(version) {
    if (document.getElementById('update-banner')) return;

    const banner = document.createElement('div');
    banner.id = 'update-banner';
    banner.style.cssText = `
        background: linear-gradient(90deg, #ef4444, #dc2626);
        color: white;
        padding: 10px 20px;
        text-align: center;
        font-size: 0.9rem;
        font-weight: 700;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
        z-index: 9999;
        position: fixed;
        top: 60px;
        left: 0;
        right: 0;
        animation: slideDown 0.5s ease-out;
    `;

    banner.innerHTML = `
        <span id="banner-text" style="display:flex; align-items:center; gap:8px;">🚀 ¡Nueva versión disponible! <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:4px; font-size:0.8rem;">${version}</span></span>
        <div id="banner-actions" style="display:flex; gap:10px;">
            <button onclick="startDirectUpdate(this)" style="background:white; color:#dc2626; border:none; text-decoration:none; padding:5px 12px; border-radius:6px; font-size:0.8rem; font-weight:800; cursor:pointer;">Actualizar ahora</button>
            <button onclick="omitUpdate()" style="background:transparent; border:1px solid rgba(255,255,255,0.5); color:white; padding:4px 10px; border-radius:6px; cursor:pointer; font-size:0.75rem;">Omitir</button>
        </div>
        <style>
            @keyframes slideDown { from { transform: translateY(-100%); } to { transform: translateY(0); } }
            @keyframes spin { 100% { transform: rotate(360deg); } }
        </style>
    `;

    document.body.prepend(banner);
}

async function startDirectUpdate(btn) {
    if (!confirm('¿Deseas instalar las mejoras ahora? Se reiniciará la aplicación al terminar.')) return;

    const banner = document.getElementById('update-banner');
    const actions = document.getElementById('banner-actions');
    const text = document.getElementById('banner-text');

    btn.disabled = true;
    btn.innerHTML = '<span style="display:inline-block; animation: spin 1s linear infinite;">⏳</span> Instalando...';

    try {
        // Obtener token CSRF
        const csrfRes = await fetch('/api/csrf-token');
        const csrfData = await csrfRes.json();
        const csrfToken = csrfData.csrf_token;

        const res = await fetch('/api/admin/apply_update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ skip: [] })
        });

        const data = await res.json();
        if (data.ok) {
            text.innerHTML = '✅ ¡Actualización completada! Reiniciando...';
            actions.innerHTML = '';
            banner.style.background = 'linear-gradient(90deg, #22c55e, #16a34a)';
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            alert('Error al actualizar: ' + (data.error || 'Error desconocido'));
            btn.disabled = false;
            btn.innerHTML = 'Actualizar ahora';
        }
    } catch (e) {
        console.error("Error en actualización directa:", e);
        alert('Error de conexión al intentar actualizar.');
        btn.disabled = false;
        btn.innerHTML = 'Actualizar ahora';
    }
}

function omitUpdate() {
    // Guardar la versión omitida en localStorage (persiste entre sesiones)
    const banner = document.getElementById('update-banner');
    const versionSpan = banner?.querySelector('#banner-text span');
    if (versionSpan) {
        localStorage.setItem('update-omitted-version', versionSpan.textContent.trim());
    }
    if (banner) banner.remove();
}

function addUpdateBadgeToConfig() {
    // Buscar enlaces a configuración en el navbar y botones de la página de configuración
    const configLinks = document.querySelectorAll('a[href*="configuracion"], .nav-link[title="Configuración"], div[onclick*="actualizaciones"]');

    configLinks.forEach(configLink => {
        if (!configLink.querySelector('.update-badge')) {
            configLink.style.position = 'relative';
            // Update link to go directly to updates section
            configLink.href = "/configuracion#actualizaciones";

            const badge = document.createElement('span');
            badge.className = 'update-badge';

            // Adjust position if it's a dashboard card
            const isDashboardCard = configLink.classList.contains('nav-btn');
            const offset = isDashboardCard ? '5px' : '-5px';

            badge.style.cssText = `
                position: absolute;
                top: ${offset};
                right: ${offset};
                background: #ef4444;
                color: white;
                font-size: 0.7rem;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                z-index: 10;
            `;
            badge.textContent = '1';
            configLink.appendChild(badge);
        }
    });

    // Añadir animación de pulso (solo una vez si no existe)
    if (!document.getElementById('badge-pulse-style')) {
        const style = document.createElement('style');
        style.id = 'badge-pulse-style';
        style.textContent = `
            @keyframes badgePulse {
                0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
                70% { transform: scale(1.1); box-shadow: 0 0 0 5px rgba(239, 68, 68, 0); }
                100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
            }
            .update-badge { animation: badgePulse 2s infinite; }
        `;
        document.head.appendChild(style);
    }
}

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavigation);
} else {
    initNavigation();
}

// Actualizar icono del toggle cuando cambia el tema
function updateDarkModeToggle() {
    const btn = document.querySelector('.dark-mode-toggle');
    if (btn) {
        btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
    }
}

// Observar cambios en el atributo data-theme
const observer = new MutationObserver(updateDarkModeToggle);
observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

// Actualizar al cargar
setTimeout(updateDarkModeToggle, 100);

async function confirmExitApp() {
    // Eliminada la confirmación para que sea automático según petición del usuario
    try {
        // Intento de cerrar el servidor
        await fetch('/api/exit', {
            method: 'POST',
            headers: { 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || '' }
        });

        // Mostrar mensaje de despedida
        document.body.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; background:linear-gradient(135deg, #001f3f, #003366); color:white; font-family:'Inter', sans-serif; text-align:center; padding: 20px;">
                <div style="font-size:5rem; margin-bottom: 20px; animation: wave 2s infinite;">👋</div>
                <h1 style="font-size:2.5rem; margin-bottom: 10px;">¡Hasta pronto!</h1>
                <p style="font-size:1.1rem; max-width: 500px; line-height: 1.5; color: rgba(255,255,255,0.8);">
                    La aplicación se está cerrando y el servidor se ha detenido de forma segura.
                </p>
                <div style="margin-top: 30px; background: rgba(255,255,255,0.1); padding: 15px 25px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2);">
                    <p style="margin:0; font-weight: 600;">La ventana se cerrará automáticamente.</p>
                    <p style="margin:5px 0 0 0; font-size: 0.85rem; opacity: 0.7;">Si la ventana no desaparece, ya puedes cerrarla manualmente.</p>
                </div>
            </div>
            <style>
                @keyframes wave { 0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(-20deg); } 75% { transform: rotate(20deg); } }
                body { margin: 0; overflow: hidden; }
            </style>
        `;

        // Intentos de cierre automático (varios métodos por compatibilidad)
        setTimeout(() => {
            window.opener = self;
            window.close();

            // Intento adicional si sigue abierta
            setTimeout(() => {
                if (!window.closed) {
                    window.open('', '_self', '');
                    window.close();
                }
            }, 500);
        }, 1500);
    } catch (e) {
        console.error("Error al cerrar la aplicación:", e);
        // Fallar silenciosamente o mostrar error si es crítico
    }
}
// Global Keyboard Shortcuts (Enter to confirm, Esc to close)
document.addEventListener('keydown', (e) => {
    // Find any visible modal
    const activeModal = Array.from(document.querySelectorAll('.modal-overlay, .modal, .modal-wrapper')).find(m => {
        const style = window.getComputedStyle(m);
        return (style.display !== 'none' && style.visibility !== 'hidden' && m.offsetHeight > 0);
    });

    if (!activeModal) return;

    if (e.key === 'Escape') {
        // Find close button: .modal-close, .modal-close-btn, .close, .btn-outline, .btn-secondary, .btn-cancel
        const closeBtn = activeModal.querySelector('.modal-close, .modal-close-btn, .close, .btn-outline, .btn-secondary, .btn-cancel') ||
            Array.from(activeModal.querySelectorAll('button')).find(b =>
                b.textContent.toLowerCase().includes('cerrar') ||
                b.textContent.toLowerCase().includes('cancelar') ||
                b.textContent.includes('✕') ||
                b.textContent.includes('×')
            );
        if (closeBtn) {
            closeBtn.click();
        } else {
            activeModal.style.display = 'none';
        }
    } else if (e.key === 'Enter') {
        // Don't trigger if in a textarea or if a button is already focused (to avoid double click)
        if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'BUTTON') return;

        // Find the primary button (success, primary, save, or common naming patterns)
        const confirmBtn = activeModal.querySelector('.btn-success, .btn-primary, .btn-confirm, .btn-save, .btn-save-task') ||
            Array.from(activeModal.querySelectorAll('button')).find(b =>
                b.textContent.toLowerCase().includes('confirmar') ||
                b.textContent.toLowerCase().includes('guardar') ||
                b.textContent.toLowerCase().includes('aceptar') ||
                b.textContent.toLowerCase().includes('importar') ||
                b.textContent.toLowerCase().includes('añadir')
            );

        if (confirmBtn) {
            e.preventDefault();
            confirmBtn.click();
        }
    }
});
