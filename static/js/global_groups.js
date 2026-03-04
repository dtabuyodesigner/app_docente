// --- GLOBAL GROUP SELECTOR LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    // Check if we have the select element in the DOM
    if (document.getElementById('globalGroupSelect')) {
        loadGroupSelectorData();
    }
});

async function loadGroupSelectorData() {
    console.log("Loading global groups...");
    try {
        // Fetch active group
        const activeRes = await fetch('/api/grupo_activo');
        if (!activeRes.ok) throw new Error(`HTTP error! status: ${activeRes.status}`);
        const activeData = await activeRes.json();

        // Fetch all groups
        const groupsRes = await fetch('/api/grupos');
        if (!groupsRes.ok) throw new Error(`HTTP error! status: ${groupsRes.status}`);
        const groups = await groupsRes.json();

        const select = document.getElementById('globalGroupSelect');
        if (!select) {
            return;
        }

        if (groups.length === 0) {
            select.innerHTML = '<option value="">Sin grupos asignados</option>';
            select.disabled = true;
            return;
        }

        select.innerHTML = groups.map(g => `<option value="${g.id}">${g.nombre}</option>`).join('');

        if (activeData.id) {
            select.value = activeData.id;
        }
    } catch (e) {
        console.error("Error loading groups:", e);
    }


}

async function changeActiveGroup(groupId) {
    console.log("Changing active group to:", groupId);
    if (!groupId) return;
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
