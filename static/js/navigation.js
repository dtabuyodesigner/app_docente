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
                <a href="/logout" class="nav-link" title="Salir" style="color: #ff4d4d">🚪</a>
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
