# 🎯 Implementación del Sistema Dual de Evaluación (Opción C)

## 📋 Resumen Ejecutivo

Se ha implementado un **sistema híbrido automático** que detecta el modo de evaluación del área y muestra la interfaz apropiada. Esta implementación es **compatible con Linux y Windows**, no rompe código existente, y proporciona una experiencia de usuario unificada.

**Fecha de implementación:** Marzo 2026  
**Archivos creados/modificados:** 4  
**Líneas de código añadidas:** ~800

## 🎯 Los 3 Modos de Evaluación

| Modo | Interfaz | Ideal para | Tabla de datos | Escala |
|------|----------|------------|----------------|--------|
| `POR_ACTIVIDADES` | Grid de actividades → propaga a criterios | Primaria/Secundaria | `evaluaciones_actividad` | 1-4 (2.5-10) |
| `POR_ACTIVIDADES` | Grid de actividades → propaga a criterios | **Infantil** | `evaluaciones_actividad` | **NI/EP/CO o PA/AD/MA** |
| `POR_SA` | Criterios dentro de SDA | Programación tradicional | `evaluaciones` (con sda_id) | Según etapa |
| `POR_CRITERIOS_DIRECTOS` | Criterios directos sin SDA | **Infantil** | `evaluacion_criterios` | **NI/EP/CO o PA/AD/MA** |

## 🎨 Detección Automática de Etapa

El sistema **detecta automáticamente la etapa educativa** desde el grupo seleccionado:

```python
# Backend (evaluacion_cuaderno.py)
grupo = cur.execute("SELECT etapa_id FROM grupos WHERE id = ?", (grupo_id,)).fetchone()
etapa_nombre = cur.execute("SELECT nombre FROM etapas WHERE id = ?", (etapa_id,)).fetchone()

if etapa_nombre == "Infantil":
    # Forzar escala infantil
    tipo_escala = "INFANTIL_NI_EP_C"  # o INFANTIL_PA_A_MA
    escala_labels = ["NI", "EP", "CO"]  # o ["PA", "AD", "MA"]
    escala_niveles = [1, 2, 3]
else:
    # Primaria/Secundaria
    tipo_escala = "NUMERICA_1_4"
    escala_labels = ["1", "2", "3", "4"]
    escala_niveles = [1, 2, 3, 4]
```

### Escalas de Evaluación por Etapa

#### Infantil (3 niveles)
- **NI/EP/CO**: No Iniciado / En Proceso / Conseguido
- **PA/AD/MA**: Parcialmente Adquirido / Adquirido / Muy Adquirido

#### Primaria/Secundaria (4 niveles)
- **1** → 2.5 (Insuficiente)
- **2** → 5.0 (Suficiente)
- **3** → 7.5 (Notable)
- **4** → 10.0 (Sobresaliente)

## 📁 Archivos Modificados/Creados

### 1. **Nuevo: `routes/evaluacion_cuaderno.py`** (450 líneas)
Endpoint unificado que centraliza toda la lógica de evaluación:

- **`/api/evaluacion/cuaderno`** (GET): Devuelve datos unificados según el modo
- **`/api/evaluacion/guardar_unificado`** (POST): Guarda evaluaciones en la tabla correcta

**Características principales:**
- Detección automática del modo desde `areas.modo_evaluacion`
- Soporte para mapeo `actividad_criterio` (muchos-a-muchos)
- Cálculo automático de medias por alumno
- Propagación actividades → criterios con o sin mapeo explícito

### 2. **Modificado: `static/evaluacion.html`** (+350 líneas)
Se han añadido funciones JavaScript para la vista híbrida:

- `cargarCuadernoUnificado()`: Carga datos según el modo
- `renderVistaActividades()`: Renderiza grid de actividades
- `guardarActividad()`: Guarda evaluación de actividad con propagación
- `mostrarResumenActividades()`: Muestra árbol visual actividades→criterios→medias
- `actualizarMediasUI()`: Actualiza las medias en tiempo real

**Nuevo botón:** "📊 Ver Resumen Actividades" - Solo visible en modo POR_ACTIVIDADES

### 3. **Modificado: `static/ayuda.html`** (+150 líneas)
Nueva sección de documentación accesible desde el menú de ayuda:

- Explicación de los 3 modos
- Guía paso a paso para cambiar el modo
- Ejemplo práctico con cálculos
- Escalas de evaluación por etapa

### 4. **Modificado: `app.py`** (+5 líneas)
- Registro del nuevo blueprint `evaluacion_cuaderno_bp`
- Exención CSRF para el nuevo endpoint

### 5. **Nuevo: `SISTEMA_DUAL_EVALUACION.md`**
Documentación técnica completa del sistema.

## 🔄 Flujo de Evaluación por Actividades

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Profesor selecciona área con modo POR_ACTIVIDADES          │
│  2. Sistema muestra actividades de las SDAs del trimestre      │
│  3. Profesor evalúa cada actividad (nivel 1-4 o 1-3 Infantil)  │
│  4. Backend guarda en evaluaciones_actividad                   │
│  5. Backend propaga automáticamente a evaluaciones (criterios) │
│  6. Sistema calcula medias y actualiza UI                      │
└─────────────────────────────────────────────────────────────────┘
```

### Propagación con Mapeo Explícito

Si existe la tabla `actividad_criterio`:
```sql
-- Solo las actividades mapeadas a un criterio afectan su nota
SELECT AVG(ea.nota)
FROM evaluaciones_actividad ea
JOIN actividad_criterio ac ON ea.actividad_id = ac.actividad_id
WHERE ac.criterio_id = X
```

### Propagación por Defecto (sin mapeo)

Si NO existe mapeo explícito:
```sql
-- Todas las actividades de la SDA afectan a todos sus criterios
SELECT AVG(ea.nota)
FROM evaluaciones_actividad ea
JOIN sda_criterios sc ON ea.sda_id = sc.sda_id
WHERE sc.criterio_id = X
```

## 🎨 Interfaz de Usuario

### Vista de Actividades (POR_ACTIVIDADES)

```
┌─────────────────────────────────────────────────────────────────┐
│  Actividad  │  Descripción / Criterios       │  Nivel          │
│─────────────│────────────────────────────────│─────────────────│
│  #1         │  Lectura del cuento            │  [1] [2] [3] [4]│
│             │  📌 SDA: Los medios            │                 │
│             │  🎯 L.1.1  🎯 L.1.2            │                 │
│─────────────│────────────────────────────────│─────────────────│
│  #2         │  Dibujo personajes             │  [1] [2] [3] [4]│
│             │  📌 SDA: Los medios            │                 │
│             │  🎯 L.2.1                      │                 │
└─────────────────────────────────────────────────────────────────┘

📊 Media criterios: 7.50
📈 Resultado del Área: 7.50

[📊 Ver Resumen Actividades]  ← Botón nuevo
```

### Resumen Visual (Modal)

Al hacer clic en "Ver Resumen Actividades":

```
┌───────────────────────────────────────────────────────────────┐
│  📊 Resumen de Evaluación por Actividades                    │
│  Alumno: Juan García                                         │
│  Área: Lengua | Trimestre: T1                                │
├───────────────────────────────────────────────────────────────┤
│  📁 SDA: Los medios de comunicación                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  ⚡ 1. Lectura del cuento                               │ │
│  │     Nivel: 3 → Nota: 7.50                              │ │
│  │     Criterios: L.1.1 (media: 7.50)  L.1.2 (media: 5.0) │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  ⚡ 2. Dibujo personajes                                │ │
│  │     Nivel: 2 → Nota: 5.00                              │ │
│  │     Criterios: L.2.1 (media: 5.00)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────┤
│           📈 NOTA FINAL DEL ÁREA: 6.67                       │
└───────────────────────────────────────────────────────────────┘
```

## 🔧 Configuración de Áreas

Para cambiar el modo de evaluación de un área:

### Opción A: Desde la UI
1. Ir a Evaluación → Área deseada
2. Click en "⚙️" junto al badge del modo
3. Seleccionar nuevo modo
4. Guardar

### Opción B: SQL Directo
```sql
-- Para Infantil (usar POR_CRITERIOS_DIRECTOS)
UPDATE areas SET modo_evaluacion = 'POR_CRITERIOS_DIRECTOS'
WHERE nombre = 'Lengua - Infantil';

-- Para Primaria (usar POR_ACTIVIDADES)
UPDATE areas SET modo_evaluacion = 'POR_ACTIVIDADES'
WHERE nombre = 'Lengua - Primaria';

-- Para usar el sistema tradicional SDA
UPDATE areas SET modo_evaluacion = 'POR_SA'
WHERE nombre = 'Matemáticas';
```

## 🧪 Testing

### Probar el endpoint unificado

```bash
# Con autenticación (desde navegador con sesión activa)
curl "http://localhost:5000/api/evaluacion/cuaderno?area_id=1&trimestre=1"

# Debería devolver JSON con:
# - modo: "POR_ACTIVIDADES" | "POR_SA" | "POR_CRITERIOS_DIRECTOS"
# - area: { id, nombre, tipo_escala, modo_evaluacion }
# - alumnos: [...]
# - criterios: [...]
# - actividades: [...] (solo POR_ACTIVIDADES)
# - sdas: [...] (solo POR_SA)
# - evaluaciones: { "{alumno}_{criterio/actividad}": nivel }
# - medias: { "{alumno_id}": { "criterios": {...}, "area": X.XX } }
```

### Verificar propagación

1. Crear SDA con actividades
2. Vincular criterios a la SDA
3. Opcional: crear mapeo `actividad_criterio`
4. Evaluar actividades desde la UI
5. Verificar que `evaluaciones` (sda_id=NULL) se actualiza
6. Comprobar media del área

## 📊 Estructura de Datos

### Tablas Involucradas

```sql
-- Evaluación por actividades (nuevo comportamiento)
evaluaciones_actividad:
  - alumno_id, actividad_id, nivel, nota, trimestre

-- Evaluación de criterios (resultado de propagación)
evaluaciones:
  - alumno_id, area_id, trimestre, criterio_id, nivel, nota
  - sda_id IS NULL para evaluación directa/propagada

-- Mapeo actividad-criterio (opcional pero recomendado)
actividad_criterio:
  - actividad_id, criterio_id
```

### Flujo de Datos

```
actividades_sda ──┬──> evaluaciones_actividad ──> evaluaciones
                  │         (nivel, nota)        (sda_id=NULL)
                  │                                  │
                  └──> actividad_criterio ──────────┘
                         (mapeo opcional)
```

## 🚀 Ventajas de esta Implementación

1. **No rompe código existente**: Los endpoints antiguos siguen funcionando
2. **Detección automática**: El profesor no tiene que seleccionar modo manualmente
3. **Flexibilidad total**: Cada área puede tener su propio modo
4. **Propagación inteligente**: Usa mapeo explícito si existe, o por defecto si no
5. **Resumen visual**: Los profesores ven claramente cómo se calculan las notas
6. **Compatible Linux/Windows**: Todo el código es multiplataforma

## ⚠️ Consideraciones

### Para Infantil
- Usar `POR_CRITERIOS_DIRECTOS` con escala `INFANTIL_NI_EP_C` o `INFANTIL_PA_A_MA`
- No es necesario crear actividades, evaluación directa de criterios

### Para Primaria
- Usar `POR_ACTIVIDADES` con escala `NUMERICA_1_4`
- Crear SDA → Actividades → Evaluar actividades
- El sistema propaga automáticamente

### Migración de Datos
Si ya hay evaluaciones en `evaluaciones_actividad`:
- No es necesario migrar nada
- El nuevo sistema es compatible con datos existentes
- La propagación se hace en tiempo real

## 📝 Próximas Mejoras (Opcional)

- [ ] Exportar resumen actividades a PDF
- [ ] Informes personalizados por alumno con árbol actividades→criterios
- [ ] Estadísticas de evaluación por actividad (cuántos alumnos evaluados)
- [ ] Sugerencias de actividades basadas en criterios no evaluados
- [ ] Historial de evaluaciones por actividad (línea de tiempo)

## 🆘 Soporte

Si encuentras errores:
1. Revisar logs de Flask en consola
2. Verificar que `areas.modo_evaluacion` tenga valores válidos
3. Comprobar que las tablas existen en la BD
4. Revisar consola del navegador (F12) para errores JS

---

**Implementado:** Marzo 2026
**Autor:** Asistente de Código IA
**Versión:** 1.0
