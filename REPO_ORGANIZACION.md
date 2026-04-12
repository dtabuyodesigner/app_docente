# 📋 REORGANIZACIÓN DEL REPOSITORIO - 9 Abril 2026

## Resumen de acciones realizadas

### 1. Merge a Master
- **Rama integrada:** `feature/modulo-reuniones-unificado` → `master`
- **Commits incorporados:**
  - `4205a4c` Mejoras en reuniones de ciclo
  - `f07a4a1` Fix pestañas Reuniones en sección Gestión

### 2. Estado actual del repo
- **Rama activa:** `master` (v1.1.30)
- **Commits recientes (master):**
  - `e387e0a` docs: actualizar a v1.1.30, merge feature/modulo-reuniones-unificado a master
  - `f07a4a1` fix: eliminar pestañas Reuniones de sección Gestión
  - `4205a4c` Mejoras en reuniones de ciclo

### 3. Ramas locales existentes
| Rama | Estado |
|------|--------|
| `master` | ✅ Actualizada con últimos cambios |
| `feature/modulo-reuniones-unificado` | Fusionada (historial conservado) |
| `feature/biblioteca-prestamos-grupos` | Antigua (sin push reciente) |
| `feature/refactor-evaluacion-curricular` | Antigua |
| Otras feature/* | Ramas antiguas sin activity reciente |

### 4. Cambios destacados de la fusión
- ✅ Nuevo archivo: `static/reuniones_plantillas.html`
- ✅ Mejoras en PDF reuniones de ciclo
- ✅ Selector de ciclo en reuniones
- ✅ Diseño mejorado del claustro en configuración
- ✅ Eliminación de pestañas redundantes de Reuniones en sección Gestión

---

## 5. Limpieza realizada - 10 Abril 2026

### Archivos eliminados
- `app.db`, `app_evaluar.db`, `cuaderno_tutor.db` (archivos vacíos)
- `__pycache__/`, `.pytest_cache/`, `.claude/`, `.qwen/`

### Archivosmovidos
- CSVs de raíz → `data/`: pilar_t3_*.csv, plantilla_*.csv, test_sda6_DEE.csv

### Nueva estructura
```
/data/                      ← CSVs de datos
/backups/                   ← Backups de base de datos
/static/                   ← Archivos estáticos
/templates/                 ← Plantillas HTML
/routes/                   → Rutas de la app
/utils/                    → Utilidades
/tests/                    → Tests
/scripts/                  → Scripts de gestión
/schemas/                  → Esquemas
/CRITERIOS_EVALUACION_INFANTIL/
/PROGRAMACIONES/
/logs/
/files/
```

---

*Documento actualizado el 10 de Abril de 2026*