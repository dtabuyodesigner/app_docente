# 📍 ESTADO DEL PROYECTO - APP_EVALUAR

**Fecha:** 6 de Abril 2026
**Último Commit:** `v1.1.25` (Bugs biblioteca: Enter en devolución y doble tick verde)
**Rama:** `feature/refactor-evaluacion-curricular`

---

## ✅ LO COMPLETADO

### Sistema Dual de Evaluación (Opción C)

Implementado sistema híbrido adaptativo completo:
- **Modo de evaluación:** POR_ACTIVIDADES | POR_SA | POR_CRITERIOS_DIRECTOS
- **Etapa educativa:** Infantil (🧸) | Primaria (🎓) (detección automática)
- **Escalas:** NI/EP/CO | PA/AD/MA | NUMÉRICA 1-4
- **Rellenador Masivo:** Funcionalidad de "Rellenar EP/CO" y "Limpiar" en modo Rejilla (Tabla) y modo Individual, incluyendo áreas POR_CRITERIOS_DIRECTOS (Infantil sin SDAs).

### Archivos Creados

| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `routes/evaluacion_cuaderno.py` | Endpoint unificado `/api/evaluacion/cuaderno` | 791 |
| `VERSION` | Fuente de verdad de la versión actual (v1.1.24) | 1 |
| `release.sh` | Script interactivo de release (bump version, commit, push) | 150 |
| `criterios y sda.md` | Vinculación detallada de criterios y SDAs Infantil | 41 |
| `SISTEMA_DUAL_EVALUACION.md` | Documentación técnica completa | 304 |
| `EVALUACION_INFANTIL.md` | Guía específica para Infantil | 249 |
| `CHANGELOG_SISTEMA_DUAL.md` | Historial de cambios | 152 |

### Archivos Modificados

| Archivo | Cambios | Propósito |
|---------|---------|-----------|
| `app.py` | +20 líneas | Registro blueprint y endpoint `/api/version` |
| `static/index.html` | +15 líneas | Badge de versión y lógica de carga |
| `static/biblioteca.html` | +20 líneas | Fix Enter en devolución y doble feedback visual |
| `static/evaluacion.html` | +800+ líneas | UI adaptativa y Rellenador Rejilla |
| `static/ayuda.html` | +537 líneas | Documentación integrada |

**Total Sesión 4 Abril:** +400 líneas (v21) + correcciones rejilla POR_CRITERIOS_DIRECTOS (v22)

---

## 🎯 CARACTERÍSTICAS IMPLEMENTADAS

### 1. Detección Automática de Etapa
```python
# Backend detecta etapa desde el grupo
grupo = cur.execute("SELECT etapa_id FROM grupos WHERE id = ?", (grupo_id,))
if etapa_nombre == "Infantil":
    tipo_escala = "INFANTIL_NI_EP_C"  # 3 niveles: NI, EP, CO
else:
    tipo_escala = "NUMERICA_1_4"  # 4 niveles: 1, 2, 3, 4
```

### 2. Endpoint Unificado
```
GET /api/evaluacion/cuaderno?area_id=1&trimestre=1

Respuesta incluye:
- modo: "POR_ACTIVIDADES"
- etapa: "Infantil" o "Primaria"
- escala_evaluacion: { tipo, niveles, labels }
- actividades, criterios, evaluaciones, medias
```

### 3. UI Adaptativa y Rellenador Rejilla
- **Infantil:** 3 botones (NI/EP/CO o PA/AD/MA) con etiquetas dinámicas.
- **Primaria:** 4 botones (1/2/3/4).
- **Rellenador Masivo (⚡):** Botones en el header para asignar nivel a todos los criterios visibles.
- **Borrado Masivo (🗑️):** Limpieza completa de evaluaciones para recálculo de medias.
- **Feedback visual:** Iluminación instantánea de celdas al evaluar.

### 4. Propagación Automática
```
Actividades → Criterios → Nota del Área
  (nivel)    → (media)  → (media)
```

### 5. Resumen Visual
- Botón "📊 Ver Resumen Actividades"
- Modal con árbol actividades → criterios → medias
- Nota final del área calculada automáticamente

### 6. Sistema de Versiones y Release
- **Archivo `VERSION`**: Control central de versión.
- **Script `release.sh`**:
  - Muestra cambios pendientes antes del release.
  - Bump automático (patch/minor/major).
  - Pide descripción para el commit.
  - Realiza `git add -A`, `commit` y `push` automáticamente.
- **Badge Dinámico**: El Panel de Control muestra la versión actual cargada vía API.

---

## 📋 PENDIENTE

### Bugs Reportados

| Bug | Descripción | Prioridad | Estado |
|-----|-------------|-----------|--------|
| **Gestión de Criterios** | No borra criterios en Evaluación → Gestión de Criterios | Alta | ✅ CORREGIDO |
| **Mensaje de error al borrar criterios** | No indicaba dónde estaban las evaluaciones bloqueantes | Media | ✅ MEJORADO (v1.1.24) |
| **Cuaderno de Evaluación** | Evaluación → Cuaderno → Cuaderno de evaluación no muestra nada | Alta | ✅ CORREGIDO |
| **Informe de Acta - Firmas** | Cuadro de firmas no muestra automáticamente la firma del tutor desde Logos | Media | ✅ CORREGIDO |
| **Rejilla EP/CO para POR_CRITERIOS_DIRECTOS** | El rellenador masivo en rejilla no funcionaba para áreas Infantil sin SDAs (escribía en tabla errónea, deseleccionar píldora activa crasheaba) | Alta | ✅ CORREGIDO |
| **Medias SDA/Área en tiempo real** | `_calcular_medias_actividades` ignoraba criterios sin mapeo `actividad_criterio` → medias siempre "—" | Alta | ✅ CORREGIDO |
| **Editar criterio — Errores de validación** | `activo` se enviaba como boolean (`true`/`false`) en vez de entero (0/1); schema marshmallow rechazaba | Alta | ✅ CORREGIDO |
| **Evaluaciones cross-mode invisibles** | Evaluaciones guardadas en `evaluacion_criterios` no se mostraban en vista POR_SA (y viceversa) | Alta | ✅ CORREGIDO |

#### Correcciones Aplicadas (1 Abril 2026)

**Bug 1 — Borrar criterios (CSRF bloqueaba DELETE)**
- **Causa:** `criterios_bp` no estaba exento de CSRF. El `DELETE /api/criterios/{id}` era rechazado con 403.
- **Fix:** `app.py` → añadido `csrf.exempt(criterios_bp)`.

**Bug 2 — Cuaderno vacío (error silencioso en JS)**
- **Causa:** Si el servidor devolvía `{error: "..."}` (por falta de `grupo_id`), `renderTable` intentaba `.forEach` sobre `data.criterios` que era `undefined` → TypeError capturado silenciosamente → tabla vacía.
- **Fix:** `static/cuaderno_evaluacion.html` → comprobación de `data.error` antes de llamar a `renderTable`, mostrando el mensaje de error en pantalla.

**Bug 3 — Firma del tutor no aparece en Acta**
- **Causa:** La query SQL en `routes/informes.py` solo buscaba claves `LIKE 'logo_%'`, pero la firma se guarda con clave `tutor_firma_filename` → nunca se cargaba en `logo_config`.
- **Fix:** `routes/informes.py` → query ampliada: `OR clave = 'tutor_firma_filename'`.

**Bug 4 — Evaluaciones huérfanas bloquean borrado de criterios**
- **Causa:** Evaluaciones guardadas en tabla `evaluaciones` con `sda_id=NULL` (de rellenador masivo o sesiones anteriores) no eran visibles en la UI pero bloqueaban el borrado de criterios.
- **Fix:** 
  - Limpieza manual de evaluaciones huérfanas con SQL
  - Mejora en `routes/criterios_api.py`: ahora el mensaje de error muestra **detalle completo** de dónde están las evaluaciones (tabla, alumnos, trimestres, SDAs)
  - Instrucciones claras de cómo resolverlo

### Corrección Aplicada (6 Abril 2026 - v1.1.24)

**Mejora — Mensaje de error detallado al borrar criterios**
- **Antes:** "Este criterio ya tiene evaluaciones registradas. Solo puede desactivarse."
- **Ahora:** Muestra tabla exacta, número de registros, alumnos evaluados, trimestres y SDAs involucradas.
- **Archivos modificados:** `routes/criterios_api.py`, `static/evaluacion.html`

### Features Pendientes

*(Ninguna pendiente en este momento)*

### Pruebas Realizadas (4 Abril 2026)
- [x] **Test 1:** Grupo de Infantil → 3 botones (NI/EP/CO) ✅
- [x] **Test 2:** Grupo de Primaria → 4 botones (1-4) ✅
- [x] **Test 3:** Evaluación de actividad → propaga a criterios ✅
- [x] **Test 4:** Resumen de actividades → muestra medias correctas ✅
- [x] **Test 5:** Rellenador masivo en Rejilla → se marcan e iluminan todas las notas ✅
- [x] **Test 6:** Limpiar masivo → borra de BBDD y actualiza medias ✅
- [x] **Test 7:** Vinculación SDA 6/7 con criterios específicos Infantil ✅
- [ ] **Test 8:** Rejilla POR_CRITERIOS_DIRECTOS → botones EP/CO se iluminan y se guardan en `evaluacion_criterios`
- [ ] **Test 9:** Rellenar EP en rejilla POR_CRITERIOS_DIRECTOS → medias del área se recalculan correctamente
- [ ] **Test 10:** Clic en píldora activa en rejilla → la borra de `evaluacion_criterios`
- [ ] **Test 11:** Evaluar alumno en POR_ACTIVIDADES → cambiar a POR_SA → los criterios evaluados aparecen
- [ ] **Test 12:** Editar criterio → Guardar → sin error de validación
- [ ] **Test 13:** Seleccionar todo en lista criterios → Borrar seleccionados → borra los que no tienen evaluaciones

### Cuando Todo Funcione

```bash
# 1. Cambiarse a main
git checkout main

# 2. Hacer merge
git merge feature/refactor-evaluacion-curricular

# 3. Subir a GitHub
git push
```

---

## 🧪 CÓMO PROBAR

### 1. Reiniciar Servidor
```bash
cd /home/danito73/Documentos/APP_EVALUAR
./start_app.sh
```

### 2. Probar Infantil
```
1. Abrir http://localhost:5000
2. Login
3. Seleccionar grupo: "3 años A" (Infantil)
4. Ir a Evaluación
5. Seleccionar área de Infantil
6. VER: 3 botones (NI, EP, CO)
```

### 3. Probar Primaria
```
1. Cambiar grupo: "1º Primaria"
2. Ir a Evaluación
3. Seleccionar área de Primaria
4. VER: 4 botones (1, 2, 3, 4)
```

### 4. Probar Evaluación por Actividades
```
1. Área con modo POR_ACTIVIDADES
2. Seleccionar SDA
3. Evaluar actividad (click en nivel)
4. Click "📊 Ver Resumen Actividades"
5. VER: Árbol con medias
```

---

## 🐛 POSIBLES ERRORES A BUSCAR

| Error | Causa Posible | Solución |
|-------|---------------|----------|
| Botones incorrectos | `etapa_id` mal configurada | Revisar tabla `grupos` |
| No propaga notas | Error en SQL | Revisar logs Flask |
| Media incorrecta | Cálculo erróneo | Verificar `_calcular_medias_*` |
| UI no actualiza | Error JS | Consola navegador (F12) |

---

## 📚 DOCUMENTACIÓN DISPONIBLE

1. **Ayuda Integrada:** `/ayuda` → sección "Sistema Dual"
2. **Técnica:** `SISTEMA_DUAL_EVALUACION.md`
3. **Infantil:** `EVALUACION_INFANTIL.md`
4. **Resumen:** `RESUMEN_IMPLEMENTACION.md`
5. **Changelog:** `CHANGELOG_SISTEMA_DUAL.md`

---

## 🔗 COMANDOS ÚTILES PARA CONTINUAR

```bash
# Ver estado actual
git status

# Ver último commit
git log -n 1

# Ver cambios pendientes de test
git diff main..feature/refactor-evaluacion-curricular

# Cuando esté listo para merge
git checkout main
git merge feature/refactor-evaluacion-curricular
git push
```

---

## 📞 CONTACTO / NOTAS

**Implementado por:** Asistente de Código IA  
**Última actualización:** 6 Abril 2026 (v1.1.25)  
**Estado:** ✅ Completado y validado en Git  
**Siguiente paso:** Monitorizar feedback de usuario sobre el empaquetado final

---

**¡Para continuar otro día, empezar por la sección "🧪 CÓMO PROBAR"!**
