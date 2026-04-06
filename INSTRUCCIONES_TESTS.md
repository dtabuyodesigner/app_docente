# 🧪 INSTRUCCIONES DE TESTS — Tests 8-13

**Fecha:** 6 Abril 2026
**Versión:** v1.1.26

---

## Antes de empezar

```bash
cd /home/danito73/Documentos/APP_EVALUAR
./start_app.sh
# Abrir http://localhost:5000
# Login como admin
```

---

## Test 8: Rejilla POR_CRITERIOS_DIRECTOS — Botones EP/CO se iluminan y guardan

**Objetivo:** Verificar que en modo POR_CRITERIOS_DIRECTOS (Infantil), los botones se iluminan y guardan en `evaluacion_criterios`.

**Pasos:**
1. Seleccionar grupo de **Infantil** (ej: "3 años A")
2. Ir a **Evaluación → Cuaderno**
3. Seleccionar un área de **Infantil** con modo `POR_CRITERIOS_DIRECTOS`
4. Seleccionar **Trimestre 1**
5. Seleccionar un alumno
6. Hacer clic en el botón **EP** (nivel 2) de cualquier criterio
7. **VERIFICAR:** El botón se ilumina en amarillo/verde
8. Cambiar de alumno y volver al anterior
9. **VERIFICAR:** El botón EP sigue iluminado (persiste en BD)

**SQL de verificación:**
```sql
sqlite3 ~/.cuadernodeltutor/app_evaluar.db "
SELECT ec.alumno_id, a.nombre as alumno, c.codigo, ec.nivel, ec.periodo
FROM evaluacion_criterios ec
JOIN alumnos a ON ec.alumno_id = a.id
JOIN criterios c ON ec.criterio_id = c.id
WHERE c.area_id = (SELECT id FROM areas WHERE nombre LIKE '%Infantil%' LIMIT 1)
ORDER BY ec.id DESC LIMIT 10;
"
```

**Resultado esperado:** ✅ Botón iluminado, dato en `evaluacion_criterios`

---

## Test 9: Rellenar EP → Medias recalculan

**Objetivo:** Verificar que al usar el rellenador masivo, las medias del área se recalculan.

**Pasos:**
1. Mismo contexto que Test 8 (Infantil, POR_CRITERIOS_DIRECTOS)
2. Ir a vista **Rejilla/Tabla** (si hay toggle)
3. Hacer clic en botón **⚡ Rellenar EP** (o similar)
4. Confirmar el diálogo
5. **VERIFICAR:** Todas las celdas EP se iluminan
6. **VERIFICAR:** La media del área se actualiza (no muestra "—")

**SQL de verificación:**
```sql
sqlite3 ~/.cuadernodeltutor/app_evaluar.db "
SELECT ec.alumno_id, a.nombre, ROUND(AVG(ec.nota), 2) as media
FROM evaluacion_criterios ec
JOIN alumnos a ON ec.alumno_id = a.id
JOIN criterios c ON ec.criterio_id = c.id
WHERE c.area_id = (SELECT id FROM areas WHERE nombre LIKE '%Infantil%' LIMIT 1)
GROUP BY ec.alumno_id;
"
```

**Resultado esperado:** ✅ Medias calculadas correctamente

---

## Test 10: Clic en píldora activa → Borra de evaluacion_criterios

**Objetivo:** Verificar que hacer clic en una píldora ya activa la desactiva (borra).

**Pasos:**
1. Mismo contexto que Test 8
2. Evaluar un criterio con **EP** (nivel 2)
3. Verificar que el botón EP está iluminado
4. Hacer **clic nuevamente** en el botón EP iluminado
5. **VERIFICAR:** El botón se desilumina
6. Cambiar de alumno y volver
7. **VERIFICAR:** El botón sigue desiluminado (borrado de BD)

**SQL de verificación:**
```sql
sqlite3 ~/.cuadernodeltutor/app_evaluar.db "
SELECT COUNT(*) as deberia_ser_0
FROM evaluacion_criterios
WHERE alumno_id = (SELECT id FROM alumnos LIMIT 1)
AND criterio_id = (SELECT id FROM criterios LIMIT 1);
"
```

**Resultado esperado:** ✅ Píldora desactivada, registro borrado de BD

---

## Test 11: Evaluar POR_ACTIVIDADES → Cambiar a POR_SA → Aparecen criterios

**Objetivo:** Verificar cross-mode: evaluaciones guardadas en modo actividades se ven en modo SA.

**Pasos:**
1. Seleccionar grupo de **Primaria**
2. Ir a **Evaluación → Cuaderno**
3. Seleccionar un área con modo **POR_ACTIVIDADES**
4. Seleccionar un alumno y evaluar una actividad (clic en nivel)
5. Ir a **Gestión → Áreas** y cambiar el modo del área a **POR_SA**
6. Volver a **Evaluación → Cuaderno**
7. Seleccionar la misma área y alumno
8. **VERIFICAR:** Los criterios muestran las evaluaciones propagadas desde actividades

**SQL de verificación:**
```sql
sqlite3 ~/.cuadernodeltutor/app_evaluar.db "
-- Evaluaciones de actividades propagadas a criterios
SELECT e.alumno_id, e.criterio_id, c.codigo, e.nivel, e.nota
FROM evaluaciones e
JOIN criterios c ON e.criterio_id = c.id
WHERE e.sda_id IS NULL  -- Propagadas desde actividades
ORDER BY e.id DESC LIMIT 10;
"
```

**Resultado esperado:** ✅ Criterios evaluados aparecen en modo POR_SA

---

## Test 12: Editar criterio → Guardar → Sin error de validación

**Objetivo:** Verificar que editar un criterio no da error de validación por `activo` boolean vs int.

**Pasos:**
1. Ir a **Evaluación → Gestión de Criterios**
2. Filtrar por un área
3. Hacer clic en **Editar** de cualquier criterio
4. Cambiar la descripción
5. Hacer clic en **Guardar**
6. **VERIFICAR:** No aparece error de validación
7. Recargar la página
8. **VERIFICAR:** El cambio persiste

**SQL de verificación:**
```sql
sqlite3 ~/.cuadernodeltutor/app_evaluar.db "
SELECT id, codigo, descripcion, activo, updated_at
FROM criterios
ORDER BY updated_at DESC LIMIT 5;
"
```

**Resultado esperado:** ✅ Guardado sin errores

---

## Test 13: Seleccionar todo → Borrar → Solo borra sin evaluaciones

**Objetivo:** Verificar que al borrar criterios seleccionados, solo se borran los que no tienen evaluaciones.

**Pasos:**
1. Ir a **Evaluación → Gestión de Criterios**
2. Seleccionar varios criterios (checkbox)
3. Hacer clic en **Borrar seleccionados**
4. Confirmar el diálogo
5. **VERIFICAR:** 
   - Criterios sin evaluaciones → borrados ✅
   - Criterios con evaluaciones → NO borrados, mensaje de error detallado ✅
6. El mensaje de error debe indicar:
   - Tabla exacta (`evaluaciones`, `evaluaciones_log` o `evaluacion_criterios`)
   - Número de registros
   - Alumnos evaluados
   - Trimestres/periodos

**Resultado esperado:** ✅ Borrado selectivo con mensaje detallado

---

## Resumen de resultados

| Test | Estado | Notas |
|------|--------|-------|
| Test 8  | ⬜ Pendiente | |
| Test 9  | ⬜ Pendiente | |
| Test 10 | ⬜ Pendiente | |
| Test 11 | ⬜ Pendiente | |
| Test 12 | ⬜ Pendiente | |
| Test 13 | ⬜ Pendiente | |

---

**Notas:**
- Test 9: **Bug corregido** — ahora se recalculan medias tras rellenado masivo
- Test 10: Ya implementado en código (líneas 1650-1653 de evaluacion.html)
- Test 12: Ya corregido en v1.1.22 (schema Boolean)
- Test 13: Ya mejorado en v1.1.24 (mensaje detallado)
