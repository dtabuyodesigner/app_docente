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
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; background:#003366; color:white; font-family:sans-serif;">
                    <h1 style="font-size:3rem;">👋 ¡Hasta luego!</h1>
                    <p>La aplicación se está cerrando y el servidor se ha detenido.</p>
                    <p style="color:rgba(255,255,255,0.6); font-size:0.8rem;">Ya puedes cerrar esta pestaña/ventana.</p>
                </div>
            `;
            
            // Intentar cerrar la ventana (solo funcionará si fue abierta por script o PWA)
            setTimeout(() => {
                window.close();
            }, 1500);
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
