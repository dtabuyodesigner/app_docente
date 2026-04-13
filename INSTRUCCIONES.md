# INSTRUCCIONES.md — Cuaderno del Tutor (APP_EVALUAR)

> Este archivo es para TODOS los asistentes de código: Antigravity, Claude, Codex, Qwen o cualquier otro. Léelo siempre antes de empezar a trabajar en este proyecto.

## Reglas generales

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

- **Repo:** `github.com/dtabuyodesigner/app_docente` (branch `feature/refactor-evaluacion-curricular`)
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

**Ejemplo de pregunta al usuario:**

> Antes de planificar, necesito que me confirmes:
> 1. ¿Qué día empieza y termina el periodo?
> 2. ¿Qué días no lectivos hay? (festivos, puentes, jornadas del centro...)
> 3. ¿Cuántas sesiones de esta área hay cada día de la semana?

### Procedimiento paso a paso

#### Paso 1: Leer el Word/ODT original

Extraer:
- Títulos de las SDAs y sus nombres
- Criterios de evaluación con descriptor completo
- Competencias específicas con descriptor completo
- Saberes básicos relacionados
- Actividades con título y número de sesiones
- Lista de sesiones de cada actividad (título y descripción)

#### Paso 2: Preguntar el calendario y calcular slots

Preguntar a Daniel las fechas, no lectivos y sesiones por día. Generar la lista cronológica de fechas lectivas y contar el total de sesiones disponibles.

#### Paso 3: Cuadrar sesiones con slots

- Si sesiones del Word == slots disponibles → asignación directa.
- Si sesiones del Word > slots → recortar fusionando sesiones similares (avisar a Daniel).
- Si sesiones del Word < slots → ampliar añadiendo sesiones coherentes (avisar a Daniel).

SA5 va primero, SA6 después. Buscar un punto de corte natural entre semanas.

#### Paso 4: Mostrar el plan ANTES de generar

Presentar una tabla con: Fecha | Día | Nº sesiones | Actividad | Título de la sesión. **Esperar confirmación** antes de generar archivos.

#### Paso 5: Generar el CSV

Una fila por sesión, todas las columnas obligatorias rellenas, respetando todas las reglas de arriba.

#### Paso 6: Generar el Word relleno con fechas

Daniel quiere conservar el Word actualizado con las fechas asignadas como referencia visual.

#### Paso 7: Verificar antes de entregar

Ejecutar este script de comprobación:

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

### Ejemplo de fila completa

```
Primaria;Matemáticas;3;MA_SA5;SDA 5 – El reloj de la clase;;MAT5.1;Lee las horas en punto y las medias horas en relojes analógicos y digitales.;CE2;Modelizar y representar la realidad utilizando conceptos y herramientas matemáticas para analizar la información, tomar decisiones y resolver problemas.;B. Sentido de la medida: Medida del tiempo: unidades (hora, minuto). Lectura de relojes analógicos y digitales (horas en punto y medias). Asociación de horas con rutinas.;MA_5.1;Construcción y lectura del reloj;;7;;;;06/04/2026;1;Construimos nuestro reloj;Cada alumno construye su reloj de cartulina con manecillas móviles.;;
```

### Errores comunes a evitar

1. ❌ No prefijar los IDs → la app mezcla actividades entre áreas.
2. ❌ Olvidar el "SDA N – " en el título → la app no muestra el número de SDA.
3. ❌ Dejar vacíos los descriptores de criterios o competencias.
4. ❌ Usar guion corto `-` en vez de guion largo `–` en "SDA N – ".
5. ❌ Inventar nombres de área que no existen literalmente en la app.
6. ❌ Repetir IDs entre áreas distintas sin prefijar.
7. ❌ Generar archivos sin enseñar primero el plan a Daniel.
8. ❌ Asumir el calendario lectivo o los días no lectivos sin preguntar: cambian según trimestre, curso, comunidad autónoma y centro.

---

## Agentes especializados

En la carpeta `.agents/` del proyecto hay agentes especializados. Son archivos `.md` con instrucciones para adoptar un rol concreto. Úsalos cuando el tipo de tarea lo requiera.

| Archivo | Nombre | Cuándo usarlo |
|---------|--------|---------------|
| `cirujano.md` | Cirujano del código | Arreglar bugs tocando lo mínimo, sin reescribir archivos enteros. **El más usado del día a día.** |
| `arquitecto-backend.md` | Arquitecto backend | Crear o modificar rutas Flask, APIs, queries SQLite, lógica de servidor. |
| `desarrollador-frontend.md` | Desarrollador frontend | Tocar HTML, CSS o JavaScript. |
| `revisor-de-codigo.md` | Revisor de código | Revisar cambios antes de hacer commit. Buscar errores, código muerto, inconsistencias. |
| `optimizador-de-datos.md` | Optimizador de datos | Cuando la app va lenta o una query tarda. Optimizar índices y consultas SQLite. |
| `ingeniero-de-seguridad.md` | Ingeniero de seguridad | Auditar vulnerabilidades, revisar autenticación, preparar una versión para publicar. |

### Cómo activar un agente

Decirle al asistente (da igual si es Antigravity, Claude, Codex o Qwen):

> *"Lee el archivo .agents/cirujano.md y úsalo para arreglar el bug de..."*

o simplemente:

> *"Actúa como el cirujano del código y arregla..."*

Si no se indica ningún agente, el asistente trabaja como generalista siguiendo las reglas de este archivo.
