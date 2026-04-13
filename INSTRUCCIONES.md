# INSTRUCCIONES.md — Cuaderno del Tutor (APP_EVALUAR)

> Este archivo es para TODOS los asistentes de código: Antigravity, Claude, Codex, Qwen o cualquier otro. Léelo siempre antes de empezar a trabajar en este proyecto.

## Reglas generales
- Da siempre respuestas en español
- Piensa antes de actuar. Lee los archivos existentes antes de escribir código.
- Sé conciso en la salida pero exhaustivo en el razonamiento.
- Prefiere editar archivos a reescribirlos enteros.
- No releas archivos que ya hayas leído salvo que el archivo pueda haber cambiado.
- Prueba tu código antes de darlo por terminado.
- Nada de aperturas aduladoras ni relleno de cierre.
- Mantén las soluciones simples y directas.
- Las instrucciones de Daniel siempre tienen prioridad sobre este archivo.

---

## Qué es este proyecto

Aplicación web de gestión docente ("Cuaderno del Tutor") en Flask + SQLite + pywebview, empaquetada con PyInstaller para Windows. La usa Pilar (maestra de 1.º de Primaria) en su portátil Windows 11 para programar, evaluar y gestionar su clase.

- **Repo:** `github.com/dtabuyodesigner/app_docente`
- **Stack:** Flask, SQLite, PyInstaller, JavaScript vanilla
- **Carpeta de trabajo:** `~/Documentos/APP_EVALUAR`
- **Estructura de archivos:** `static/` para HTML, `routes/` para Python
- **DB personal:** fuera del proyecto, en `~/.cuadernodeltutor/app_evaluar.db`
- **Distribución:** ZIP con `.exe` (PyInstaller) o futuro instalador Inno Setup

---

## Convenciones del proyecto

- Los comandos Git siempre deben especificar si son para Linux o Windows.
- Los commits no deben incluir comandos `cp` — los archivos se guardan directamente en su carpeta correcta.
- Cuando Antigravity, Qwen u otro asistente proporcione versiones alternativas de un archivo, comparar contra el original antes de adoptar.
- Windows puede requerir `git clone --single-branch` para evitar problemas de nombres de archivo en el historial.

---

## Workflow Git

### Rama antes de cualquier modificación

Antes de tocar código, **crear siempre una rama**. Nunca trabajar directamente en `master`.

```bash
git checkout -b fix/descripcion-corta      # para correcciones
git checkout -b feat/descripcion-corta     # para nuevas funcionalidades
```

Al terminar y verificar que todo funciona, hacer merge a `master`.

### Formato de commits (Conventional Commits)

```
fix: descripción corta del fix
feat: descripción corta de la nueva funcionalidad
docs: cambios en documentación
refactor: refactor sin cambio funcional
```

### Comandos habituales

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

## Gestión de versiones

### Versión — subir en cada modificación

**Archivos a actualizar siempre juntos:**

- `VERSION` → número sin `v` (ej: `1.1.33`)
- `version.py` → `APP_VERSION = "v1.1.33"`

Incremento por tipo de cambio:
- **Patch** (x.x.**N**): fix de bug, ajuste menor, retoque de UI
- **Minor** (x.**N**.0): nueva funcionalidad, módulo nuevo
- **Major** (**N**.0.0): cambio de arquitectura, refactor completo

Se puede usar el script `./release.sh` para hacer bump + commit + push automático.

### Actualizar ESTADO_ACTUAL.md

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

Actualizar también la línea de pie:
```
**Última actualización:** DD Mes YYYY — descripción breve
```

### Actualizar la ayuda

Si la modificación añade una funcionalidad nueva, cambia un flujo existente o elimina algo, **actualizar `static/ayuda.html`** para reflejar el cambio.

Criterio: si un usuario que no sabe nada de la modificación lo necesitaría saber para usar la app → actualizar la ayuda.

### Checklist antes de hacer merge a master

- [ ] `python -m pytest tests/` pasa sin errores
- [ ] La app arranca correctamente con `./start_app.sh`
- [ ] Versión subida en `VERSION` y `version.py`
- [ ] `ESTADO_ACTUAL.md` actualizado con fecha y hora
- [ ] `CHANGELOG.md` actualizado con la nueva entrada
- [ ] `static/ayuda.html` actualizado si el cambio lo requiere
- [ ] Commits con formato Conventional Commits

---

## Conversión de programaciones Word/ODT → CSV

La app importa programaciones didácticas desde CSV. Este es el procedimiento exacto para generar esos CSV a partir de un Word o ODT de programación.

### Formato del CSV

- **Separador:** punto y coma (`;`)
- **Codificación:** UTF-8
- **24 columnas en este orden exacto:**

```
Etapa;Area;Trimestre;SDA_ID;SDA_Titulo;Duracion_Semanas;Criterio_Codigo;Criterio_Descriptor;Competencia_Codigo;Competencia_Descriptor;Saberes_Basicos;Actividad_ID;Actividad_Titulo;Actividad_Descripcion;Actividad_Sesiones;Semana_Numero;Semana_Titulo;Dia;Fecha;Sesion_Numero;Sesion_Titulo;Descripcion_Sesion;Material;Evaluable
```

**Una fila por sesión** (no por actividad ni por SDA). Si una actividad tiene 7 sesiones, genera 7 filas repitiendo los datos de SDA, criterio, competencia y actividad en cada una.

### Reglas críticas (no negociables)

#### 1. Áreas literales

El campo `Area` debe coincidir EXACTAMENTE con el nombre del área en la app. Si no coincide, la app crea un área nueva o mete el contenido en otra. Áreas válidas confirmadas:

- `Lengua Castellana y Literatura`
- `Matemáticas`
- `Conocimiento del Medio Natural, Social y Cultural`

Respetar tildes, mayúsculas y comas exactamente. Si se programa otra área, preguntar a Daniel el nombre literal.

#### 2. IDs únicos por área (CRÍTICO)

La app agrupa por `SDA_ID` y `Actividad_ID`. Si dos CSV de áreas distintas usan los mismos IDs (ej: `SA5`, `5.1`), la app mezcla las actividades entre áreas. **Solución:** prefijar todos los IDs con un código de área de 2 letras:

| Área | Prefijo | Ejemplo SDA_ID | Ejemplo Actividad_ID |
|------|---------|----------------|----------------------|
| Cono | `CO_` | `CO_SA5` | `CO_5.1` |
| Lengua | `LE_` | `LE_SA5` | `LE_5.1` |
| Matemáticas | `MA_` | `MA_SA5` | `MA_5.1` |

#### 3. Títulos de SDA con prefijo "SDA N – "

Para que la app muestre el número de la SDA en el listado, el `SDA_Titulo` debe empezar con `SDA N – ` (con guion largo `–` U+2013):

- ✅ `SDA 5 – Nos movemos por Canarias`
- ❌ `Nos movemos por Canarias`
- ❌ `SDA 5 - Nos movemos por Canarias` (guion corto)

#### 4. Rellenar SIEMPRE los descriptores completos

Estas columnas no pueden quedar vacías:

- `Criterio_Descriptor`: texto completo del criterio de evaluación.
- `Competencia_Codigo`: código de la competencia específica asociada (ej: `CE2`).
- `Competencia_Descriptor`: texto completo de la competencia específica.
- `Saberes_Basicos`: bloque de saberes básicos de la SDA correspondiente.

#### 5. Formato de fecha

`dd/mm/aaaa` (ejemplo: `06/04/2026`).

#### 6. Columnas que se dejan vacías

Estas se dejan en blanco (entre `;;`) salvo indicación contraria:

`Duracion_Semanas`, `Semana_Numero`, `Semana_Titulo`, `Dia`, `Material`, `Evaluable`, `Actividad_Descripcion`.

#### 7. Sesiones por actividad

- `Actividad_Sesiones`: número total de sesiones de esa actividad (mismo valor en todas sus filas).
- `Sesion_Numero`: correlativo dentro de la actividad (1, 2, 3...).

### Calendario lectivo

**IMPORTANTE: NO asumir fechas ni días no lectivos.** El calendario cambia según el trimestre, el curso académico, la comunidad autónoma y el centro. Antes de empezar, **preguntar SIEMPRE a Daniel**:

1. **Fecha de inicio y fin** del periodo a programar.
2. **Días no lectivos** dentro del periodo (festivos, puentes, jornadas del centro...).
3. **Sesiones por día de la semana** del área a programar (ej: Lunes 1, Martes 2, Jueves 1).

Solo después de tener estos tres datos confirmados se puede generar la lista de fechas disponibles.

### Procedimiento paso a paso

1. **Leer el Word/ODT original** — Extraer SDAs, criterios, competencias, saberes, actividades y sesiones.
2. **Preguntar el calendario** — Fechas, no lectivos y sesiones por día.
3. **Cuadrar sesiones con slots** — Si sobran, fusionar; si faltan, ampliar (siempre avisar a Daniel).
4. **Mostrar el plan ANTES de generar** — Tabla Fecha | Día | Sesiones | Actividad | Título. Esperar confirmación.
5. **Generar el CSV** — Una fila por sesión, respetando todas las reglas.
6. **Generar el Word relleno con fechas** — Como referencia visual para Daniel.
7. **Verificar antes de entregar** — Ejecutar el script de comprobación:

```python
import csv
PATH = 'archivo.csv'
with open(PATH, encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    rows = list(reader)

assert len(reader.fieldnames) == 24, f"Cabecera tiene {len(reader.fieldnames)} columnas, debe tener 24"
for i, r in enumerate(rows, 2):
    assert r['Area'] in ('Lengua Castellana y Literatura','Matemáticas','Conocimiento del Medio Natural, Social y Cultural'), f"Fila {i}: área inválida"
    assert r['SDA_ID'][:3] in ('CO_','LE_','MA_'), f"Fila {i}: SDA_ID sin prefijo de área"
    assert r['Actividad_ID'][:3] in ('CO_','LE_','MA_'), f"Fila {i}: Actividad_ID sin prefijo de área"
    assert r['SDA_Titulo'].startswith('SDA '), f"Fila {i}: SDA_Titulo sin prefijo 'SDA N – '"
    assert r['Criterio_Descriptor'], f"Fila {i}: Criterio_Descriptor vacío"
    assert r['Competencia_Codigo'], f"Fila {i}: Competencia_Codigo vacío"
    assert r['Competencia_Descriptor'], f"Fila {i}: Competencia_Descriptor vacío"
    assert r['Saberes_Basicos'], f"Fila {i}: Saberes_Basicos vacío"
print(f"OK: {len(rows)} filas válidas")
```

### Errores comunes a evitar

1. ❌ No prefijar los IDs → la app mezcla actividades entre áreas.
2. ❌ Olvidar el "SDA N – " en el título → la app no muestra el número de SDA.
3. ❌ Dejar vacíos los descriptores de criterios o competencias.
4. ❌ Usar guion corto `-` en vez de guion largo `–` en "SDA N – ".
5. ❌ Inventar nombres de área que no existen literalmente en la app.
6. ❌ Repetir IDs entre áreas distintas sin prefijar.
7. ❌ Generar archivos sin enseñar primero el plan a Daniel.
8. ❌ Asumir el calendario lectivo o los días no lectivos sin preguntar.

---

## Archivos clave

| Archivo | Propósito |
|---------|-----------|
| `VERSION` | Versión en texto plano (fuente de verdad) |
| `version.py` | `APP_VERSION` para la app Flask |
| `ESTADO_ACTUAL.md` | Estado actual del proyecto |
| `CHANGELOG.md` | Historial completo de cambios por versión |
| `static/ayuda.html` | Ayuda integrada en la app |
| `schema.sql` | Esquema base de datos |
| `utils/db.py` | Migraciones automáticas al arrancar |
| `utils/backup.py` | Backup diario automático (corre antes de migraciones) |
| `routes/` | Un archivo por módulo |
| `static/` | HTML, CSS, JS del frontend |
| `data/` | CSVs de importación/exportación |

---

## Agentes especializados

En la carpeta `.agents/` del proyecto hay agentes especializados. Son archivos `.md` con instrucciones para adoptar un rol concreto.

| Archivo | Nombre | Cuándo usarlo |
|---------|--------|---------------|
| `cirujano.md` | Cirujano del código | Arreglar bugs tocando lo mínimo. **El más usado del día a día.** |
| `arquitecto-backend.md` | Arquitecto backend | Crear o modificar rutas Flask, APIs, queries SQLite. |
| `desarrollador-frontend.md` | Desarrollador frontend | Tocar HTML, CSS o JavaScript. |
| `revisor-de-codigo.md` | Revisor de código | Revisar cambios antes de hacer commit. |
| `optimizador-de-datos.md` | Optimizador de datos | Cuando la app va lenta o una query tarda. |
| `ingeniero-de-seguridad.md` | Ingeniero de seguridad | Auditar vulnerabilidades, revisar autenticación. |
| `tester-calidad.md` | Tester de Calidad | Verificar que todo funciona antes de merge a master. **Siempre antes de release.** |

### Cómo activar un agente

> *"Lee el archivo .agents/cirujano.md y úsalo para arreglar el bug de..."*

o simplemente:

> *"Actúa como el cirujano del código y arregla..."*

Si no se indica ningún agente, el asistente trabaja como generalista siguiendo las reglas de este archivo.
