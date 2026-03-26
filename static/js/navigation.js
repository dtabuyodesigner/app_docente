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
            { name: "Reuniones", icon: "👨‍👩‍👧‍👦", url: "/reuniones" }
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
    checkUpdates();
}

async function checkUpdates() {
    try {
        const res = await fetch('/api/admin/check_updates');
        const data = await res.json();
        if (data.ok && data.update_available) {
            showUpdateBanner(data.current_version);
            addUpdateBadgeToConfig();
        }
    } catch (e) {
        console.error("Error al comprobar actualizaciones:", e);
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
        z-index: 10000;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        animation: slideDown 0.5s ease-out;
    `;
    
    banner.innerHTML = `
        <span style="display:flex; align-items:center; gap:8px;">🚀 ¡Nueva versión disponible! <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:4px; font-size:0.8rem;">${version}</span></span>
        <div style="display:flex; gap:10px;">
            <a href="/configuracion#actualizaciones" style="background:white; color:#dc2626; text-decoration:none; padding:5px 12px; border-radius:6px; font-size:0.8rem; font-weight:800;">Actualizar ahora</a>
            <button onclick="this.parentElement.parentElement.remove()" style="background:transparent; border:1px solid rgba(255,255,255,0.5); color:white; padding:4px 10px; border-radius:6px; cursor:pointer; font-size:0.75rem;">Omitir</button>
        </div>
        <style>
            @keyframes slideDown { from { transform: translateY(-100%); } to { transform: translateY(0); } }
        </style>
    `;
    
    document.body.prepend(banner);
}

function addUpdateBadgeToConfig() {
    const configLinks = document.querySelectorAll('a[href*="configuracion"]');
    
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

async function confirmExitApp() {
    if (confirm("¿Estás seguro de que deseas cerrar la aplicación por completo? El servidor se detendrá.")) {
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
                        <p style="margin:0; font-weight: 600;">Ya puedes cerrar esta pestaña manualmente.</p>
                        <p style="margin:5px 0 0 0; font-size: 0.85rem; opacity: 0.7;">(Por seguridad, algunos navegadores no permiten el cierre automático)</p>
                    </div>
                </div>
                <style>
                    @keyframes wave { 0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(-20deg); } 75% { transform: rotate(20deg); } }
                    body { margin: 0; overflow: hidden; }
                </style>
            `;
            
            // Intentos de cierre automático (varios métodos por compatibilidad)
            setTimeout(() => {
                window.close(); // Método estándar
                if (window.opener) window.opener = null;
                window.open('', '_self', ''); 
                window.close();
            }, 2000);
        } catch (e) {
            console.error("Error al cerrar la aplicación:", e);
            alert("No se pudo cerrar el servidor de forma remota.");
        }
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
