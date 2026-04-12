# CLAUDE.md — Instrucciones para APP_EVALUAR

## 1. Rama antes de cualquier modificación

Antes de tocar código, **crear siempre una rama**. Nunca trabajar directamente en `master`.

```bash
git checkout -b fix/descripcion-corta      # para correcciones
git checkout -b feat/descripcion-corta     # para nuevas funcionalidades
```

Al terminar y verificar que todo funciona, hacer merge a `master`.

---

## 2. Versión — subir en cada modificación

**Archivos a actualizar siempre juntos:**

- `VERSION` → número sin `v` (ej: `1.1.33`)
- `version.py` → `APP_VERSION = "v1.1.33"`

Incremento por tipo de cambio:
- **Patch** (x.x.**N**): fix de bug, ajuste menor, retoque de UI
- **Minor** (x.**N**.0): nueva funcionalidad, módulo nuevo
- **Major** (**N**.0.0): cambio de arquitectura, refactor completo

Se puede usar el script `./release.sh` para hacer bump + commit + push automático.

---

## 3. Actualizar ESTADO_ACTUAL.md al final de cada mejora

Al terminar cualquier modificación, **añadir una nueva sección al inicio** de `ESTADO_ACTUAL.md` con este formato:

```markdown
## ✅ DESCRIPCIÓN DE LA MEJORA (vX.X.XX)

**Fecha:** DD de Mes YYYY — HH:MM

### Qué se hizo
- Punto 1
- Punto 2

### Archivos modificados
- `ruta/archivo.py` — descripción del cambio
- `static/archivo.html` — descripción del cambio
```

Actualizar también la línea de pie del archivo:
```
**Última actualización:** DD Mes YYYY — descripción breve
```

---

## 4. Actualizar la ayuda si el cambio es significativo

Si la modificación añade una funcionalidad nueva, cambia un flujo existente o elimina algo, **actualizar `static/ayuda.html`** para reflejar el cambio.

Criterio: si un usuario que no sabe nada de la modificación lo necesitaría saber para usar la app → actualizar la ayuda.

---

## 5. Checklist antes de hacer merge a master

Antes de mergear cualquier rama a `master`, verificar:

- [ ] `python -m pytest tests/` pasa sin errores
- [ ] La app arranca correctamente con `./start_app.sh`
- [ ] Versión subida en `VERSION` y `version.py`
- [ ] `ESTADO_ACTUAL.md` actualizado con fecha y hora
- [ ] `CHANGELOG.md` actualizado con la nueva entrada
- [ ] `static/ayuda.html` actualizado si el cambio lo requiere
- [ ] Commits con formato Conventional Commits

Si algún punto falla → **no mergear** hasta resolverlo.

---

## 6. Formato de commits (Conventional Commits)

El proyecto ya sigue este formato — mantenerlo siempre:

```
fix: descripción corta del fix
feat: descripción corta de la nueva funcionalidad
docs: cambios en documentación
refactor: refactor sin cambio funcional
```

---

## 6. Comandos habituales

```bash
# Arrancar la app en desarrollo
./start_app.sh
# → http://localhost:5000

# Nuevo release (bump versión + commit + push)
./release.sh

# Tests
cd /home/danito73/Documentos/APP_EVALUAR
python -m pytest tests/
```

---

## 8. Archivos clave

| Archivo | Propósito |
|---------|-----------|
| `VERSION` | Versión en texto plano (fuente de verdad) |
| `version.py` | `APP_VERSION` para la app Flask |
| `ESTADO_ACTUAL.md` | Estado actual del proyecto (solo versión presente) |
| `CHANGELOG.md` | Historial completo de cambios por versión |
| `static/ayuda.html` | Ayuda integrada en la app |
| `schema.sql` | Esquema base de datos |
| `utils/db.py` | Migraciones automáticas al arrancar |
| `utils/backup.py` | Backup diario automático (corre antes de migraciones) |
| `routes/` | Un archivo por módulo |
| `static/` | HTML, CSS, JS del frontend |
| `data/` | CSVs de importación/exportación |
