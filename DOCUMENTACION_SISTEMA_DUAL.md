# Documentación Técnica: Sistema Dual de Evaluación

Esta funcionalidad permite a los docentes elegir entre tres modos de evaluación (Por SDA, Por Criterios Directos o Por Actividades) y gestionar vínculos precisos entre actividades y criterios.

## 1. Modelo de Datos

### Tabla: `actividad_criterio`
- `actividad_id`: Relación con `actividades_sda.id`.
- `criterio_id`: Relación con `criterios.id`.

### Tabla `areas`
- El campo `modo_evaluacion` almacena la preferencia: `POR_SA`, `POR_CRITERIOS_DIRECTOS`, `POR_ACTIVIDADES`.

---

## 2. Lógica de Negocio (Backend)

### Propagación de Notas
Función: `routes/evaluacion_actividades.py` -> `_propagar_actividades_a_criterios`.
- **Flujo**: Al guardar una nota de actividad, el sistema recalcula la nota de los criterios vinculados.
- **Algoritmo**: 
    1. Si existen registros en `actividad_criterio` para un criterio, solo se promedian las actividades vinculadas.
    2. Si No existen, se promedian todas las actividades de las SDAs que contienen ese criterio (comportamiento legacy).

---

## 3. Interfaz de Usuario (Frontend)

### Modal de Programación (`static/programacion.html`)
- **`refrescarCriteriosEnActividades()`**: Función clave que sincroniza en tiempo real los códigos escritos en "Criterios" con los checkboxes de cada "Actividad".
- **Checklist dinámico**: Permite al usuario marcar/desmarcar vínculos visualmente.

### Cuaderno de Evaluación (`static/evaluacion.html`)
- Botón **"⚙️ Modo"**: Permite cambiar el origen de los datos a nivel de área.
- Vista "Por Actividades": Muestra la lista de actividades evaluables de la SDA seleccionada.
