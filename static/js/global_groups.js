// --- GLOBAL GROUP SELECTOR LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    // Attempt load, but the header might be dynamic
    checkAndLoadSelector();
});

function checkAndLoadSelector(attempts = 0) {
    if (document.getElementById('globalGroupSelect')) {
        loadGroupSelectorData();
    } else if (attempts < 10) {
        // Retry for up to 2 seconds (header injection might have a slight delay)
        setTimeout(() => checkAndLoadSelector(attempts + 1), 200);
    }
}

async function loadGroupSelectorData() {
    console.log("[Groups] Iniciando carga...");
    const select = document.getElementById('globalGroupSelect');
    if (!select) return;

    try {
        select.innerHTML = '<option value="">⚙️ Req 1...</option>';
        const activeRes = await fetch('/api/grupo_activo');
        select.innerHTML = '<option value="">⚙️ Req 2...</option>';

        // Parseo seguro: si no es JSON (ej: HTML de error/login), abortar
        const activeContentType = activeRes.headers.get('content-type') || '';
        if (!activeRes.ok || !activeContentType.includes('application/json')) {
            console.warn("[Groups] /api/grupo_activo no devolvió JSON. ¿Sesión expirada?");
            select.innerHTML = '<option value="">⚠️ Sesión no activa</option>';
            return;
        }
        const activeData = await activeRes.json();

        select.innerHTML = '<option value="">⚙️ Req 3...</option>';
        const groupsRes = await fetch('/api/grupos');
        select.innerHTML = '<option value="">⚙️ Req 4...</option>';

        const groupsContentType = groupsRes.headers.get('content-type') || '';
        if (!groupsRes.ok || !groupsContentType.includes('application/json')) {
            console.warn("[Groups] /api/grupos no devolvió JSON. ¿Sesión expirada?");
            select.innerHTML = '<option value="">⚠️ Error de sesión</option>';
            return;
        }

        const groups = await groupsRes.json();

        // VALIDACIÓN CRÍTICA: El Service Worker podría devolver un objeto de error en lugar de un array
        if (!Array.isArray(groups)) {
            console.error("[Groups] La API no devolvió un array:", groups);
            select.innerHTML = `<option value="">⚠️ ${groups.error || 'Error de datos'}</option>`;
            return;
        }

        if (groups.length === 0) {
            select.innerHTML = '<option value="">Sin grupos asignados</option>';
            select.disabled = true;
            return;
        }

        select.innerHTML = '<option value="">🌐 Todos los grupos</option>' + groups.map(g => `<option value="${g.id}">${g.nombre}</option>`).join('');
        
        if (activeData && activeData.id) {
            select.value = activeData.id;
        } else {
            select.value = "";
        }
        console.log("[Groups] Selector cargado con éxito.");
    } catch (e) {
        console.error("[Groups] Error cargando grupos:", e);
        if (select) {
            select.innerHTML = '<option value="">⚠️ Error de conexión</option>';
        }
    }
}

async function changeActiveGroup(groupId) {
    console.log("Changing active group to:", groupId);
    try {
        const res = await fetch('/api/grupo_activo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grupo_id: groupId })
        });
        if (res.ok) {
            console.log("Group changed successfully, reloading page...");
            // Reload page to reflect new group data
            window.location.reload();
        } else {
            console.error("Failed to change group:", await res.text());
        }
    } catch (e) {
        console.error("Error changing group:", e);
    }
}
