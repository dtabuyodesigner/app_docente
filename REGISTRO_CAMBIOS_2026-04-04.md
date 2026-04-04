# Registro de Cambios - Sesión de Corrección de Bugs

**Fecha:** 4 de abril de 2026  
**Módulos afectados:** `routes/evaluacion_cuaderno.py`, `routes/evaluacion_sda.py`, `static/evaluacion.html`

---

## 🐛 Bug #1: Resumen de Actividades no mostraba niveles/grades

**Descripción:** El modal "Resumen de Actividades" mostraba todos los niveles y notas como "-" a pesar de tener actividades evaluadas.

**Causa raíz:**
- El backend en modo `POR_ACTIVIDADES` devolvía evaluaciones claveadas por `criterio_id` (`{alumno_id}_{criterio_id}`)
- El frontend buscaba evaluaciones por `actividad_id` (`{alumno_id}_{actividad_id}`)
- Mismatch de claves → no encontraba evaluaciones

**Solución implementada:**
- **Archivo:** `routes/evaluacion_cuaderno.py` (líneas 194-213)
- Se modificó la sección `POR_ACTIVIDADES` para consultar la tabla `evaluaciones_actividad` y devolver las evaluaciones con el formato correcto
- Ahora las evaluaciones se devuelven como `{alumno_id}_{actividad_id}: nivel`

```python
# ANTES (incorrecto):
evaluaciones = {}
for alum_id_str, m_data in medias.items():
    if "criterios" in m_data:
        for crit_id_str, nota_media in m_data["criterios"].items():
            evaluaciones[f"{alum_id_str}_{crit_id_str}"] = int(round(nota_media))

# AHORA (correcto):
evaluaciones = {}
if actividad_ids and alumno_ids:
    act_placeholders = ",".join("?" * len(actividad_ids))
    alum_placeholders = ",".join("?" * len(alumno_ids))
    evals = cur.execute(f"""
        SELECT alumno_id, actividad_id, nivel
        FROM evaluaciones_actividad
        WHERE actividad_id IN ({act_placeholders})
          AND alumno_id IN ({alum_placeholders})
          AND trimestre = ?
    """, actividad_ids + alumno_ids + [trimestre]).fetchall()
    evaluaciones = {
        f"{e['alumno_id']}_{e['actividad_id']}": e['nivel']
        for e in evals
    }
```

---

## 🐛 Bug #2: Botones de nivel se quedaban marcados simultáneamente

**Descripción:** Al pulsar "Rellenar EP/AD" o "Rellenar CO/MA", se quedaban marcados dos botones de nivel en la misma actividad cuando solo debería haber uno activo.

**Causa raíz:**
- `guardarActividad()` no limpiaba los estilos de los botones hermanos antes de marcar el nuevo
- `cargarNotasExistentes()` intentaba marcar botones en la vista unificada usando la clase `selected`, pero los botones de esa vista usan estilos inline
- `rellenarTodos()` llamaba a `cargarNotasExistentes()` que no actualizaba los botones visuales

**Solución implementada:**

### 2a. Función `guardarActividad()` - `static/evaluacion.html` (línea ~2023)
- Ahora limpia todos los botones del contenedor antes de aplicar estilo al botón seleccionado

```javascript
// Limpiar botones hermanos antes de guardar
if (element) {
    const container = element.parentElement;
    const btns = container.querySelectorAll('button');
    const colors = esInfantil ? ['#ef4444', '#f59e0b', '#10b981'] : ['#ff4d4d', '#ffcc00', '#2ecc71', '#3498db'];
    
    // Resetear todos los botones al estado no seleccionado
    btns.forEach((btn, idx) => {
        btn.style.background = '';
        btn.style.color = '';
        btn.style.borderColor = '#e0e0e0';
    });
    
    // Aplicar estilo al botón seleccionado
    const idx = Array.from(btns).indexOf(element);
    if (idx >= 0 && idx < colors.length) {
        element.style.background = colors[idx];
        element.style.color = 'white';
        element.style.borderColor = colors[idx];
    }
}
```

### 2b. Función `cargarNotasExistentes()` - `static/evaluacion.html` (línea ~1276)
- Ahora detecta si estamos en vista unificada (botones con clase `btn-nivel-act`)
- En vista unificada, solo llama a `cargarMedia()` sin intentar marcar botones

```javascript
if (conf.modo_evaluacion === 'POR_ACTIVIDADES') {
    // Detectar si estamos en la vista unificada (renderVistaActividades)
    const botonesUnificados = document.querySelectorAll('.btn-nivel-act');
    if (botonesUnificados.length > 0) {
        // La vista unificada ya renderizó los botones con los datos correctos
        cargarMedia();
        return;
    }
    // Vista simple (renderTablaActividades) - usar el método antiguo
    // ...
}
```

### 2c. Función `rellenarTodos()` - `static/evaluacion.html` (línea ~1600)
- En modo `POR_ACTIVIDADES`, ahora llama a `cargarCuadernoUnificado()` para recargar la vista completa

```javascript
if (data.ok) {
    const conf = getAreaConfig();
    if (conf && conf.modo_evaluacion === 'POR_ACTIVIDADES') {
        cargarCuadernoUnificado();  // Recarga vista completa con botones actualizados
    } else {
        cargarNotasExistentes();
    }
    cargarMedia();
    cargarResumenAlumno();
}
```

---

## 🐛 Bug #3: Dropdown de SDA mostraba "No hay SDAs" pero cargaba actividades

**Descripción:** Al iniciar la app y seleccionar alumno, área y trimestre, el dropdown de SDA mostraba "No hay SDAs" pero sí mostraba las actividades de la primera SDA.

**Causa raíz:**
- En modo `POR_ACTIVIDADES`, la variable `sdas` nunca se llenaba en el backend
- `cargarCuadernoUnificado()` no actualizaba el dropdown de SDAs con los datos recibidos
- Se llamaba a `cargarSDA()` de forma redundante

**Solución implementada:**

### 3a. Backend: Consulta de SDAs en modo `POR_ACTIVIDADES` - `routes/evaluacion_cuaderno.py` (líneas 166-189)
- Añadida consulta de SDAs en el modo `POR_ACTIVIDADES` (antes solo existía en `POR_SA`)
- Formateo del nombre con trimestre: `[T3] Nombre de la SDA`

```python
# Obtener SDAs del área/trimestre para el dropdown
if sda_id and sda_id not in ('', 'null', '0'):
    sdas_rows = cur.execute("""
        SELECT s.id, s.nombre, s.trimestre
        FROM sda s
        WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL) AND s.id = ?
          AND (s.grupo_id = ? OR s.grupo_id IS NULL)
    """, (area_id, trimestre, sda_id, grupo_id)).fetchall()
else:
    sdas_rows = cur.execute("""
        SELECT DISTINCT s.id, s.nombre, s.trimestre
        FROM sda s
        JOIN actividades_sda a ON a.sda_id = s.id
        WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL)
          AND (s.grupo_id = ? OR s.grupo_id IS NULL)
        ORDER BY s.nombre
    """, (area_id, trimestre, grupo_id)).fetchall()

sdas = []
for s in sdas_rows:
    sda_dict = dict(s)
    if s["trimestre"]:
        sda_dict["nombre"] = f"[T{s['trimestre']}] {s['nombre']}"
    sdas.append(sda_dict)
```

### 3b. Frontend: Actualización del dropdown - `static/evaluacion.html` (líneas 1920-1950)
- `cargarCuadernoUnificado()` ahora actualiza el dropdown de SDAs con los datos del backend
- Selecciona automáticamente la primera SDA si no hay ninguna seleccionada

```javascript
// Actualizar dropdown de SDAs si estamos en modo POR_ACTIVIDADES o POR_SA
if ((data.modo === 'POR_ACTIVIDADES' || data.modo === 'POR_SA') && data.sdas) {
    const sdaSelect = document.getElementById('sdaSelect');
    if (sdaSelect && data.sdas.length > 0) {
        const sdaSeleccionada = sdaSelect.value;
        let options = '';
        data.sdas.forEach(s => { 
            const selected = (!sdaSeleccionada || sdaSeleccionada === 'null' || sdaSeleccionada === '') && s.id === data.sdas[0]?.id;
            options += `<option value="${s.id}" ${selected ? 'selected' : ''}>${s.nombre}</option>`; 
        });
        sdaSelect.innerHTML = options;
        if (!sdaSeleccionada || sdaSeleccionada === 'null' || sdaSeleccionada === '') {
            sdaSelect.selectedIndex = 0;
        }
    } else if (sdaSelect && data.sdas.length === 0) {
        sdaSelect.innerHTML = '<option value="" disabled selected>No hay SDAs</option>';
    }
}
```

### 3c. Eliminada llamada redundante a `cargarSDA()` - `static/evaluacion.html` (líneas 1126-1138)
- En modo `POR_ACTIVIDADES`, eliminada la llamada a `cargarSDA()` porque `cargarCuadernoUnificado()` ya actualiza el dropdown
- En modo `POR_SA`, también se usa `cargarCuadernoUnificado()` en lugar de `cargarSDA()`

```javascript
if (conf.modo_evaluacion === 'POR_ACTIVIDADES') {
    // Usar la nueva vista unificada de actividades (ya incluye carga de SDAs)
    cargarCuadernoUnificado();
} else if (conf.modo_evaluacion === 'POR_SA') {
    // Usar la vista unificada para POR_SA también
    cargarCuadernoUnificado();
}
```

---

## 🐛 Bug #4: Modo "Evaluar por SDA" no cargaba correctamente

**Descripción:** Al seleccionar "Evaluar por SDA", no cargaba las SDAs a la primera y mostraba una tabla plana de criterios en lugar de SDAs agrupadas.

**Causa raíz:**
- `renderVistaSDA()` solo llamaba a `cargarCriteriosSA()`, que era la función antigua
- No existía una vista visual que agrupara criterios por SDA

**Solución implementada:**

### 4a. Nueva función `renderVistaSDA()` - `static/evaluacion.html` (líneas 2215-2330)
- Renderiza SDAs agrupadas con sus criterios debajo
- Muestra cabecera de SDA con fondo azul
- Botones de nivel con colores y estilos visuales
- Soporte para SDAs sin criterios (evaluación directa)

```javascript
function renderVistaSDA(data) {
    const { sdas, criterios, evaluaciones, escala_evaluacion, alumnos } = data;
    const alumnoId = alumnos[0]?.id;
    const esInfantil = escala_evaluacion && escala_evaluacion.tipo.startsWith('INFANTIL_');
    
    // Configurar labels y niveles según etapa
    let labels, niveles, colors;
    if (esInfantil) {
        labels = ['NI/PA', 'EP/AD', 'CO/MA'];
        niveles = [1, 2, 3];
        colors = ['#ef4444', '#f59e0b', '#10b981'];
    } else {
        labels = ['1', '2', '3', '4'];
        niveles = [1, 2, 3, 4];
        colors = ['#ff4d4d', '#ffcc00', '#2ecc71', '#3498db'];
    }

    const critMap = {};
    criterios.forEach(c => { critMap[c.id] = c; });

    sdas.forEach(sda => {
        // Fila de cabecera de la SDA
        const trSda = document.createElement('tr');
        trSda.innerHTML = `<td colspan="3" style="background:#e8f4fd; color:#0056a0; font-weight:700; padding:10px 15px;">
            📚 ${sda.nombre}
        </td>`;
        tbody.appendChild(trSda);

        // Renderizar cada criterio de la SDA
        const criteriosSda = sda.criterio_ids || [];
        criteriosSda.forEach(critId => {
            const crit = critMap[critId];
            if (!crit) return;
            
            const nivelActual = evaluaciones[`${alumnoId}_${critId}`] || 0;
            // Generar botones de nivel...
        });
    });
}
```

### 4b. Nueva función `guardarCriterioSDA()` - `static/evaluacion.html` (líneas 2147-2213)
- Guarda evaluaciones de criterios en modo `POR_SA`
- URL correcta: `/api/evaluacion/sda/guardar`
- Incluye `area_id` en el payload
- Limpia botones hermanos antes de marcar

### 4c. Actualizado `cargarNotasExistentes()` - `static/evaluacion.html` (líneas 1304-1330)
- Detecta vista unificada de `POR_SA` (botones con clase `btn-nivel-sda`)
- En vista unificada, solo carga medias sin interferir

---

## 🐛 Bug #5: Error "Endpoint no encontrado" al evaluar/borrar en POR_SA

**Descripción:** Al intentar guardar una evaluación en modo POR_SA, aparecía el error "Endpoint no encontrado".

**Causa raíz:**
- `guardarCriterioSDA()` llamaba a `/api/evaluacion/guardar` que no existe
- El endpoint correcto es `/api/evaluacion/sda/guardar`
- Faltaba `area_id` en el payload

**Solución implementada:**
- **Archivo:** `static/evaluacion.html` (línea 2190)
- URL corregida: `/api/evaluacion/sda/guardar`
- Añadido `area_id` al payload
- Conversión explícita a `parseInt()`

```javascript
const res = await fetch('/api/evaluacion/sda/guardar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        alumno_id: parseInt(alumId),
        area_id: parseInt(areaId),
        criterio_id: criterio_id,
        nivel: nivel,
        sda_id: sda_id ? parseInt(sda_id) : null,
        trimestre: parseInt(trimestre)
    })
});
```

---

## ✨ Mejora #1: Evaluación directa de SDAs sin criterios

**Descripción:** Las SDAs sin criterios vinculados no podían evaluarse. Solo mostraba un mensaje informativo.

**Solución implementada:**

### 1a. Frontend: Botones de evaluación directa - `static/evaluacion.html` (líneas 2333-2375)
- Cuando una SDA no tiene criterios, muestra botones para evaluar la SDA directamente
- Nueva función `guardarSDADirecta()` para guardar evaluaciones sin criterio

```javascript
if (criteriosSda.length === 0) {
    // Permitir evaluar la SDA directamente sin criterios
    const nivelActual = evaluaciones[`${alumnoId}_0`] || 0;
    
    const botonesHtml = niveles.map((n, idx) => {
        // Generar botones...
    });
    
    trSdaEval.innerHTML = `
        <td colspan="2">
            <div style="font-weight:600;">Evaluar SDA directamente</div>
            <div style="font-size:0.8rem; color:#999; font-style:italic;">Sin criterios vinculados</div>
        </td>
        <td><div style="display:flex; gap:6px;">${botonesHtml}</div></td>
    `;
}
```

### 1b. Backend: Soporte para criterio_id = 0 - `routes/evaluacion_sda.py` (líneas 38-93)
- `guardar_evaluacion_sda()` ahora acepta `criterio_id = null` o `0`
- Usa `criterio_id = 0` para indicar evaluación directa de SDA
- Diferente constraint de unicidad para evaluaciones directas

```python
criterio_id = d.get("criterio_id")
if criterio_id is not None and criterio_id != 'null' and criterio_id != '':
    criterio_id = int(criterio_id)
else:
    criterio_id = None

# ...

if criterio_id is not None:
    # Evaluación de criterio específico dentro de una SDA
    cur.execute("""
        INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
        DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
    """, (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota))
else:
    # Evaluación directa de la SDA (sin criterio específico)
    cur.execute("""
        INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(alumno_id, sda_id, trimestre)
        DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
    """, (alumno_id, area_id, trimestre, sda_id, 0, nivel, nota))
```

---

## ✨ Mejora #2: Filtro de SDAs incluye trimestre NULL

**Descripción:** Al seleccionar área y trimestre, no se mostraban SDAs que tenían `trimestre IS NULL` en la base de datos.

**Causa raíz:**
- Las consultas SQL solo filtraban por `s.trimestre = ?`
- SDAs con `trimestre NULL` quedaban excluidas

**Solución implementada:**
- **Archivos:** `routes/evaluacion_cuaderno.py` (líneas 143-183 y 243-258)
- Todas las consultas ahora usan `(s.trimestre = ? OR s.trimestre IS NULL)`

```sql
-- ANTES:
WHERE s.area_id = ? AND s.trimestre = ?

-- AHORA:
WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL)
```

Esto aplica a:
- Consultas de actividades en modo `POR_ACTIVIDADES`
- Consultas de SDAs en modo `POR_ACTIVIDADES`
- Consultas de SDAs en modo `POR_SA`

---

## 📊 Resumen de archivos modificados

| Archivo | Líneas modificadas | Tipo |
|---------|-------------------|------|
| `routes/evaluacion_cuaderno.py` | 143-213, 243-269 | Backend: Consultas de SDAs, evaluaciones por actividad |
| `routes/evaluacion_sda.py` | 38-93 | Backend: Soporte criterio_id null |
| `static/evaluacion.html` | 1126-1138, 1276-1330, 1600-1615, 1920-1950, 2023-2213, 2215-2375 | Frontend: Vista unificada, guardado, renderizado |

---

## 🧪 Testing recomendado

1. **Resumen de Actividades:**
   - Seleccionar área con modo `POR_ACTIVIDADES`
   - Evaluar varias actividades
   - Abrir "Ver Resumen Actividades"
   - ✅ Verificar que muestra niveles y notas correctamente

2. **Botones de rellenado:**
   - Pulsar "Rellenar EP/AD" o "Rellenar CO/MA"
   - ✅ Verificar que solo un botón queda marcado por actividad
   - ✅ Verificar que los botones se iluminan correctamente

3. **Dropdown de SDAs:**
   - Seleccionar alumno, área y trimestre
   - ✅ Verificar que el dropdown de SDA se llena correctamente
   - ✅ Verificar que la primera SDA queda seleccionada

4. **Modo Evaluar por SDA:**
   - Cambiar a modo "Evaluar por SDA"
   - ✅ Verificar que se muestran SDAs agrupadas con criterios
   - ✅ Verificar que se pueden evaluar criterios
   - ✅ Verificar que SDAs sin criterios muestran botón de evaluación directa

5. **Filtro de trimestre:**
   - Seleccionar área con SDAs de diferentes trimestres
   - ✅ Verificar que se muestran SDAs del trimestre seleccionado
   - ✅ Verificar que se incluyen SDAs con `trimestre NULL`

---

## 🔧 Notas técnicas

- **Vista unificada:** Tanto `POR_ACTIVIDADES` como `POR_SA` ahora usan `cargarCuadernoUnificado()` para cargar datos
- **Detección de vista:** `cargarNotasExistentes()` detecta si está en vista unificada buscando clases específicas (`btn-nivel-act` o `btn-nivel-sda`)
- **Evaluaciones directas:** Se usa `criterio_id = 0` como convención para evaluaciones directas de SDA
- **Limpieza de botones:** Todas las funciones de guardado limpian botones hermanos antes de marcar el seleccionado

---

## 🐛 Bug #6: Modo POR_SA no cargaba evaluaciones correctamente

**Fecha:** 4 de abril de 2026 (continuación)  
**Descripción:** En modo "Evaluar por SDA", los botones de nivel no se iluminaban aunque las evaluaciones se guardaban correctamente. El dropdown de SDAs también aparecía vacío.

### Problema 6a: Dropdown no se actualizaba

**Causa raíz:**
- En `cargarCuadernoUnificado()` se usaba `document.getElementById('sdaSelect')` que no existe
- El ID correcto del elemento es `sda` (declarado en línea 438)
- La variable `sdaSelect` ya está declarada globalmente en la línea 743: `const sdaSelect = document.getElementById("sda")`

**Solución implementada:**
- **Archivo:** `static/evaluacion.html` (línea 1942)
- Eliminada la redeclaración local `const sdaSelect = document.getElementById('sdaSelect')`
- Ahora se usa la variable global `sdaSelect` que ya apunta al elemento correcto

```javascript
// ANTES (incorrecto):
if ((data.modo === 'POR_ACTIVIDADES' || data.modo === 'POR_SA') && data.sdas) {
    const sdaSelect = document.getElementById('sdaSelect');  // ❌ ID incorrecto
    // ...
}

// AHORA (correcto):
if ((data.modo === 'POR_ACTIVIDADES' || data.modo === 'POR_SA') && data.sdas) {
    // ✅ Usa la variable global sdaSelect declarada en línea 743
    console.log('[cargarCuadernoUnificado] Modo:', data.modo, 'SDAs recibidas:', data.sdas.length, sdaSelect ? 'sdaSelect encontrado' : 'sdaSelect NO encontrado');
    // ...
}
```

### Problema 6b: Evaluaciones no se cargaban

**Causa raíz:**
- **Backend:** En modo `POR_SA`, cuando no se seleccionaba un SDA específico, la consulta buscaba evaluaciones con `sda_id IS NULL`
- Pero las evaluaciones se guardaban con el `sda_id` real de la SDA
- Resultado: No se encontraban las evaluaciones al cargar el cuaderno

**Solución implementada:**
- **Archivo:** `routes/evaluacion_cuaderno.py` (líneas 301-342)
- Modificada la lógica de carga de evaluaciones para manejar tres casos:
  1. **SDA específica:** Buscar evaluaciones con ese `sda_id`
  2. **Todas las SDAs:** Buscar evaluaciones con `sda_id IN (lista_de_sda_ids)`
  3. **Sin SDAs:** Buscar evaluaciones generales del área

```python
# ANTES (incorrecto):
if sda_id and sda_id not in ('', 'null', '0'):
    evals = cur.execute(f"""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE ... AND sda_id = ? AND trimestre = ?
    """, ...).fetchall()
else:
    evals = cur.execute(f"""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE ... AND area_id = ? AND trimestre = ? AND sda_id IS NULL
    """, ...).fetchall()

# AHORA (correcto):
if sda_id and sda_id not in ('', 'null', '0'):
    # Evaluaciones para una SDA específica
    evals = cur.execute(f"""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE ... AND sda_id = ? AND trimestre = ?
    """, ...).fetchall()
elif sda_ids:
    # Evaluaciones para todas las SDAs del área/trimestre
    sda_placeholders = ",".join("?" * len(sda_ids))
    evals = cur.execute(f"""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE ... AND area_id = ? AND trimestre = ? AND sda_id IN ({sda_placeholders})
    """, ...).fetchall()
else:
    # Sin SDAs, buscar evaluaciones generales del área
    evals = cur.execute(f"""
        SELECT alumno_id, criterio_id, nivel
        FROM evaluaciones
        WHERE ... AND area_id = ? AND trimestre = ?
    """, ...).fetchall()
```

**Logs de depuración añadidos:**
- `static/evaluacion.html`: Añadidos `console.log` en:
  - `cargarCuadernoUnificado()`: Para rastrear la carga de SDAs y actualización del dropdown
  - `renderVistaSDA()`: Para verificar datos recibidos y claves de evaluaciones
  - `guardarCriterioSDA()`: Para ver qué se envía y recibe al guardar
  - Renderizado de criterios: Para verificar que `nivelActual` se calcula correctamente

---

## 🐛 Bug #7: Al cambiar de SDA se perdían las otras del dropdown

**Fecha:** 4 de abril de 2026  
**Descripción:** Cuando el usuario seleccionaba una SDA en el dropdown, al volver a abrir el dropdown solo aparecía esa SDA, imposibilitando cambiar a otra SDA.

**Causa raíz:**
- **Backend:** Cuando se pasaba `sda_id` como parámetro, la consulta SQL filtraba las SDAs y solo devolvía la SDA seleccionada
- **Frontend:** Al actualizar el dropdown con solo esa SDA, las demás desaparecían

**Solución implementada:**
- **Archivos:** 
  - `routes/evaluacion_cuaderno.py` (líneas 166-177 para `POR_ACTIVIDADES`, líneas 235-245 para `POR_SA`)
  - `static/evaluacion.html` (líneas 1938-1956)

### Backend: Siempre devolver TODAS las SDAs

```python
# ANTES (incorrecto - filtraba por sda_id):
if sda_id and sda_id not in ('', 'null', '0'):
    sdas_rows = cur.execute("""
        SELECT s.id, s.nombre, s.trimestre
        FROM sda s
        WHERE s.area_id = ? AND ... AND s.id = ?
    """, (area_id, trimestre, sda_id, grupo_id)).fetchall()

# AHORA (correcto - siempre todas las SDAs):
sdas_rows = cur.execute("""
    SELECT DISTINCT s.id, s.nombre, s.trimestre
    FROM sda s
    JOIN actividades_sda a ON a.sda_id = s.id
    WHERE s.area_id = ? AND (s.trimestre = ? OR s.trimestre IS NULL)
      AND (s.grupo_id = ? OR s.grupo_id IS NULL)
    ORDER BY s.nombre
""", (area_id, trimestre, grupo_id)).fetchall()
```

### Frontend: Preservar la selección actual

```javascript
// ANTES (incorrecto - solo seleccionaba la primera si no había selección):
data.sdas.forEach(s => {
    const selected = (!sdaSeleccionada || sdaSeleccionada === 'null' || sdaSeleccionada === '') && s.id === data.sdas[0]?.id;
    options += `<option value="${s.id}" ${selected ? 'selected' : ''}>${s.nombre}</option>`;
});

// AHORA (correcto - preserva la selección actual o selecciona la primera):
data.sdas.forEach(s => {
    const isSelected = sdaSeleccionada && sdaSeleccionada !== 'null' && sdaSeleccionada !== ''
        ? s.id == sdaSeleccionada  // Mantener selección actual
        : s.id === data.sdas[0]?.id;  // Seleccionar primera si no hay selección
    options += `<option value="${s.id}" ${isSelected ? 'selected' : ''}>${s.nombre}</option>`;
});
```

---

## 🐛 Bug #8: Error 500 al guardar evaluaciones en modo POR_SA

**Fecha:** 4 de abril de 2026  
**Descripción:** Al intentar evaluar una SDA directamente (sin criterios), aparecía un error 500 "Error de conexión".

**Causa raíz:**
- **Backend:** Se usaba `criterio_id = 0` para indicar evaluación directa de SDA, pero:
  1. La columna `criterio_id` tiene un foreign key constraint a la tabla `criterios`
  2. No existe un criterio con `id = 0`
  3. El foreign key constraint fallaba al intentar insertar

**Solución implementada:**
- **Archivos:**
  - `routes/evaluacion_sda.py` (líneas 68-95)
  - `routes/evaluacion_cuaderno.py` (líneas 324-346)
  - `static/evaluacion.html` (líneas 2253-2261, 2342-2365)

### Backend: Usar criterio_id = NULL en lugar de 0

```python
# ANTES (incorrecto - foreign key constraint falla):
if criterio_id is not None:
    cur.execute("""
        INSERT INTO evaluaciones ... (criterio_id = 0)
        ON CONFLICT(alumno_id, sda_id, trimestre) ...
    """, (..., 0, ...))

# AHORA (correcto - NULL es válido):
if criterio_id is not None and criterio_id != 0:
    # Evaluación de criterio específico
    cur.execute("""
        INSERT INTO evaluaciones ... (criterio_id = X)
        ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre) ...
    """, (..., criterio_id, ...))
else:
    # Evaluación directa de SDA
    cur.execute("""
        INSERT INTO evaluaciones ... (criterio_id = NULL)
        ON CONFLICT(alumno_id, sda_id, trimestre) ...
    """, (..., nivel, nota))
```

### Backend: Cargar evaluaciones directas de SDA

```python
# Obtener evaluaciones directas de SDA (criterio_id = NULL)
if sda_ids and alumno_ids:
    evals_direct = cur.execute(f"""
        SELECT alumno_id, sda_id, nivel
        FROM evaluaciones
        WHERE criterio_id IS NULL
          AND alumno_id IN (...)
          AND sda_id IN (...)
    """, ...).fetchall()
    
    for e in evals_direct:
        # Clave especial para evaluaciones directas
        evaluaciones[f"{e['alumno_id']}_sda_{e['sda_id']}"] = e['nivel']
```

### Frontend: Usar clave correcta para evaluaciones directas

```javascript
// ANTES (incorrecto):
const nivelActual = evaluaciones[`${alumnoId}_0`] || 0;

// AHORA (correcto):
const nivelActual = evaluaciones[`${alumnoId}_sda_${sda.id}`] || 0;
```

---

## 🐛 Bug #9: Error 500 al guardar manualmente después de usar rellenador en POR_SA

**Fecha:** 4 de abril de 2026  
**Descripción:** Después de usar los botones "Rellenar EP/AD" o "Rellenar CO/MA", al intentar cambiar manualmente el nivel de un criterio aparecía un error 500.

**Causa raíz:**
- El endpoint `guardar_evaluacion_sda` usaba `ON CONFLICT` con una cláusula que podía fallar cuando ya existían registros creados por `guardar_masivo` (usado por los botones de rellenar)
- `guardar_masivo` usa una estrategia diferente: INSERT en `evaluaciones_log`, cálculo de medias, luego DELETE + INSERT en `evaluaciones`
- `guardar_evaluacion_sda` usaba `ON CONFLICT DO UPDATE`, que podía generar conflictos con registros existentes creados por el otro endpoint
- Además, el manejo de `criterio_id = 0` causaba problemas con el foreign key constraint

**Solución implementada:**
- **Archivo:** `routes/evaluacion_sda.py` (líneas 38-102)
- Cambiada la estrategia de `ON CONFLICT DO UPDATE` a `DELETE + INSERT` (consistente con `guardar_masivo`)
- Mejor manejo de errores con logging detallado
- Validación mejorada de parámetros

```python
# ANTES (problemático con ON CONFLICT):
cur.execute("""
    INSERT INTO evaluaciones ...
    ON CONFLICT(alumno_id, criterio_id, sda_id, trimestre)
    DO UPDATE SET nivel = excluded.nivel, nota = excluded.nota
""", ...)

# AHORA (consistente con guardar_masivo):
cur.execute("DELETE FROM evaluaciones WHERE alumno_id = ? AND criterio_id = ? AND sda_id = ? AND trimestre = ?", 
           (alumno_id, criterio_id, sda_id, trimestre))
cur.execute("""
    INSERT INTO evaluaciones (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (alumno_id, area_id, trimestre, sda_id, criterio_id, nivel, nota))
```

**Mejoras adicionales:**
- Logging detallado de errores con `traceback.format_exc()`
- Mensajes de error más descriptivos en la validación de parámetros
- Manejo consistente de `criterio_id = 0` (se trata como NULL)

---

**Estado:** ✅ Corregido  
**Próximo paso:** Reiniciar la app y verificar que:
1. Se pueden usar los botones "Rellenar EP/AD" y "Rellenar CO/MA" sin errores
2. Después de rellenar, se pueden cambiar niveles manualmente sin errores 500
3. Los botones se iluminan correctamente
4. No aparecen errores en la consola del servidor

## 🐛 Bug #10: Visualización del Cuaderno Infantil (Nomenclatura PAMA, UI y Filtros)

**Fecha:** 4 de abril de 2026
**Descripción:** Se homogeneizó el uso de etiquetas de evaluación (NI/PA, EP/AD, CO/MA) según el estándar autonómico. Se introdujo un diseño de tipología 'grid' en los contenedores de botones para que aseguren cuadrículas en los de tamaños proporcionales.

También se resolvieron:
- **Llenado masivo sin feedback UI:** Se introdujo lógica para cambiar colores en tiempo real mediante manipulación directa de estilos para garantizar validación explícita sobre la carga visual.
- **Filtro del Seleccionable SDA visualmente ignorado:** Se fijó la asignación de la variable global de SDAs para posibilitar el filtrado de DOM de forma fiel en la vista de *Evaluar por SDA*.
