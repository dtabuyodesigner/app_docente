# Instrucciones para convertir programaciones Word/ODT → CSV (App Pilar / Cuaderno del Tutor)

## Contexto

App Pilar (Cuaderno del Tutor) importa programaciones didácticas desde un CSV con un formato muy concreto. Este documento explica cómo convertir un Word/ODT de programación en ese CSV evitando los errores típicos.

---

## Formato del CSV

**Separador:** punto y coma (`;`)
**Codificación:** UTF-8
**Cabeceras (en este orden exacto, 24 columnas):**

```
Etapa;Area;Trimestre;SDA_ID;SDA_Titulo;Duracion_Semanas;Criterio_Codigo;Criterio_Descriptor;Competencia_Codigo;Competencia_Descriptor;Saberes_Basicos;Actividad_ID;Actividad_Titulo;Actividad_Descripcion;Actividad_Sesiones;Semana_Numero;Semana_Titulo;Dia;Fecha;Sesion_Numero;Sesion_Titulo;Descripcion_Sesion;Material;Evaluable
```

**Una fila por sesión** (no por actividad ni por SDA). Si una actividad tiene 7 sesiones, genera 7 filas, repitiendo en cada una los datos de SDA, criterio, competencia, actividad, etc.

---

## Reglas críticas (no negociables)

### 1. Áreas literales

El campo `Area` debe coincidir EXACTAMENTE con el nombre del área en App Pilar. Si no, la app crea un área nueva o mete el contenido en otra. Áreas válidas confirmadas:

- `Lengua Castellana y Literatura`
- `Matemáticas`
- `Conocimiento del Medio Natural, Social y Cultural`

(Respetar tildes, mayúsculas y comas exactamente.)

### 2. IDs únicos por área (CRÍTICO)

App Pilar agrupa por `SDA_ID` y `Actividad_ID`. Si dos CSV de áreas distintas usan los mismos IDs (ej: `SA5`, `5.1`), la app mezcla las actividades entre áreas. **Solución:** prefijar todos los IDs con un código de área de 2 letras:

- Cono → `CO_`
- Lengua → `LE_`
- Matemáticas → `MA_`

Ejemplos:
- `CO_SA5`, `CO_SA6`, `CO_5.1`, `CO_5.2`, `CO_6.1`...
- `LE_SA5`, `LE_SA6`, `LE_5.1`, `LE_5.2`...
- `MA_SA5`, `MA_SA6`, `MA_5.1`, `MA_5.2`...

### 3. Títulos de SDA con prefijo "SDA N – "

Para que App Pilar muestre el número de la SDA en el listado, el `SDA_Titulo` debe empezar con `SDA N – ` (siendo N el número, con guion largo `–` U+2013, no guion normal `-`):

- ✅ `SDA 5 – Nos movemos por Canarias`
- ❌ `Nos movemos por Canarias`
- ❌ `SDA 5 - Nos movemos por Canarias` (guion corto)

### 4. Rellenar SIEMPRE descriptores completos

Las columnas `Criterio_Descriptor`, `Competencia_Codigo`, `Competencia_Descriptor` y `Saberes_Basicos` deben rellenarse con el texto completo extraído del Word original. **No dejarlas vacías.**

- `Criterio_Descriptor`: texto completo del criterio (no solo unas palabras).
- `Competencia_Codigo`: código de la competencia específica asociada (ej: `CE2`).
- `Competencia_Descriptor`: texto completo de la competencia.
- `Saberes_Basicos`: bloque de saberes básicos de la SDA correspondiente.

Si un criterio no tiene competencia explícita en el Word, asociar la más afín según el contenido.

### 5. Formato de fecha

`dd/mm/aaaa` (ejemplo: `06/04/2026`). Sin ceros omitidos.

### 6. Columnas que se dejan vacías

Estas columnas se dejan en blanco (entre `;;`) salvo que el usuario indique lo contrario:

- `Duracion_Semanas`
- `Semana_Numero`
- `Semana_Titulo`
- `Dia`
- `Material`
- `Evaluable`
- `Actividad_Descripcion` (la descripción va en `Descripcion_Sesion`)

### 7. Sesiones por actividad

`Actividad_Sesiones` lleva el número total de sesiones de esa actividad (mismo valor en todas las filas de la misma actividad). `Sesion_Numero` lleva el número correlativo de sesión dentro de la actividad (1, 2, 3...).

---

## Calendario lectivo

**IMPORTANTE: NO asumir fechas ni días no lectivos.** El calendario cambia según el trimestre, el curso académico, la comunidad autónoma y el centro. Antes de empezar a planificar, **preguntar SIEMPRE a Daniel**:

1. **Fecha de inicio del trimestre/periodo** (ej: 6 de abril de 2026)
2. **Fecha de fin del trimestre/periodo** (ej: 15 de junio de 2026)
3. **Días no lectivos** dentro del periodo (festivos, puentes, días del centro, vacaciones de Semana Santa si caen dentro, etc.)
4. **Sesiones por día de la semana** del área que se va a programar (ej: Lunes 1, Martes 2, Jueves 1)

Solo después de tener estos cuatro datos confirmados se puede generar la lista de slots de fechas disponibles.

**Ejemplo de pregunta inicial al usuario:**

> Antes de empezar a planificar, necesito que me confirmes:
> 1. ¿Qué día empieza y termina el periodo a programar?
> 2. ¿Qué días no lectivos hay dentro de ese periodo? (festivos, puentes, jornadas del centro...)
> 3. ¿Cuántas sesiones de esta área hay cada día de la semana? (Lunes X, Martes X...)

**Calendario de referencia conocido (3.º trimestre 2025-2026, curso de Pilar)** — usar SOLO si Daniel confirma explícitamente que es el mismo:

- Periodo: 6 de abril – 15 de junio de 2026
- No lectivos: jueves 23/04, jueves 30/04, viernes 01/05 (Día del Trabajo), lunes 04/05, lunes 01/06
- Sesiones por día de la semana de cada área (1.º Primaria de Pilar):

| Área | Lunes | Martes | Miércoles | Jueves | Viernes |
|------|-------|--------|-----------|--------|---------|
| Cono | 1 | – | 1 | 2 | – |
| Lengua | 1 | – | – | – | 3 |
| Matemáticas | 1 | 2 | – | 1 | – |

Estos datos NO se reutilizan automáticamente para otros trimestres ni cursos: hay que preguntarlos cada vez.

---

## Procedimiento paso a paso

### Paso 1: Leer el Word/ODT original

Convertir a markdown o texto plano para extraer:
- Título de las SDAs (SA5, SA6...) y su nombre
- Criterios de evaluación con su descriptor completo
- Competencias específicas con su descriptor completo
- Saberes básicos relacionados
- Actividades (5.1, 5.2, 6.1...) con título y número de sesiones
- Lista de sesiones de cada actividad (título y descripción/desarrollo)

### Paso 2: Preguntar el calendario y calcular slots disponibles

Antes de calcular nada, **preguntar a Daniel**:
1. Fecha de inicio y fin del periodo
2. Días no lectivos dentro del periodo
3. Sesiones por día de la semana del área a programar

Solo entonces, generar la lista cronológica de fechas lectivas y sumar el total de sesiones disponibles.

### Paso 3: Cuadrar sesiones del Word con slots disponibles

Comparar:
- Si **sesiones del Word == slots disponibles**: asignación directa.
- Si **sesiones del Word > slots**: recortar fusionando sesiones similares o redundantes (avisando a Daniel).
- Si **sesiones del Word < slots**: ampliar añadiendo sesiones nuevas coherentes (avisando a Daniel).

Repartir SA5 y SA6 cronológicamente: SA5 ocupa la primera mitad, SA6 la segunda. Buscar un punto de corte natural entre semanas.

### Paso 4: Antes de generar nada, mostrar el plan a Daniel

Presentar una tabla con: Fecha | Día | Sesiones | Actividad | Título de la sesión. Esperar confirmación antes de generar archivos.

### Paso 5: Generar el CSV

Una fila por sesión, rellenando todas las columnas obligatorias y respetando las reglas críticas (áreas literales, IDs prefijados, títulos con "SDA N – ", descriptores completos).

### Paso 6: Verificar el CSV antes de entregar

Comprobar:
- ✅ Cabecera correcta y 24 columnas
- ✅ Área literal exacta
- ✅ Todos los `SDA_ID` y `Actividad_ID` con prefijo de área
- ✅ Todos los `SDA_Titulo` empiezan con `SDA N – `
- ✅ `Criterio_Descriptor`, `Competencia_Codigo`, `Competencia_Descriptor` y `Saberes_Basicos` rellenos en todas las filas
- ✅ Total de filas = total de sesiones planificadas
- ✅ Fechas en formato `dd/mm/aaaa`

### Paso 7: Generar también el Word relleno con las fechas

Daniel quiere conservar el Word actualizado con las fechas asignadas para tenerlo como referencia visual además del CSV.

---

## Ejemplo de fila completa

```
Primaria;Matemáticas;3;MA_SA5;SDA 5 – El reloj de la clase;;MAT5.1;Lee las horas en punto y las medias horas en relojes analógicos y digitales.;CE2;Modelizar y representar la realidad utilizando conceptos y herramientas matemáticas para analizar la información, tomar decisiones y resolver problemas.;B. Sentido de la medida: Medida del tiempo: unidades (hora, minuto). Lectura de relojes analógicos y digitales (horas en punto y medias). Asociación de horas con rutinas.;MA_5.1;Construcción y lectura del reloj;;7;;;;06/04/2026;1;Construimos nuestro reloj;Cada alumno construye su reloj de cartulina con manecillas móviles. Materiales: cartulina, encuadernadores, rotuladores, plantilla de esfera.;;
```

---

## Errores comunes a evitar

1. ❌ **No prefijar los IDs** → la app mezcla actividades entre áreas.
2. ❌ **Olvidar el "SDA N – " en el título** → la app no muestra el número de SDA en el listado.
3. ❌ **Dejar vacíos los descriptores** de criterios o competencias.
4. ❌ **Usar guion corto `-` en vez de guion largo `–`** en `SDA N – `.
5. ❌ **Inventar nombres de área** que no existen literalmente en App Pilar.
6. ❌ **Repetir IDs** entre áreas distintas (`SA5` en cono y `SA5` en lengua sin prefijar).
7. ❌ **Empezar a generar sin enseñar primero el plan** a Daniel para que lo valide.
8. ❌ **Asumir el calendario lectivo o los días no lectivos** sin preguntar: cambian según trimestre, curso, comunidad autónoma y centro.

---

## Comprobación final con awk/python

Antes de entregar el CSV, ejecutar este comprobante mínimo:

```bash
python3 << 'EOF'
import csv
PATH = 'archivo.csv'
with open(PATH, encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    rows = list(reader)

assert len(reader.fieldnames) == 24, f"Cabecera tiene {len(reader.fieldnames)} columnas, debe tener 24"
for i, r in enumerate(rows, 2):
    assert r['Area'] in ('Lengua Castellana y Literatura','Matemáticas','Conocimiento del Medio Natural, Social y Cultural'), f"Fila {i}: área inválida"
    assert r['SDA_ID'].startswith(('CO_','LE_','MA_')), f"Fila {i}: SDA_ID sin prefijo"
    assert r['Actividad_ID'].startswith(('CO_','LE_','MA_')), f"Fila {i}: Actividad_ID sin prefijo"
    assert r['SDA_Titulo'].startswith('SDA '), f"Fila {i}: SDA_Titulo sin prefijo 'SDA N – '"
    assert r['Criterio_Descriptor'], f"Fila {i}: Criterio_Descriptor vacío"
    assert r['Competencia_Codigo'], f"Fila {i}: Competencia_Codigo vacío"
    assert r['Competencia_Descriptor'], f"Fila {i}: Competencia_Descriptor vacío"
    assert r['Saberes_Basicos'], f"Fila {i}: Saberes_Basicos vacío"

print(f"OK: {len(rows)} filas válidas")
EOF
```

Si pasa sin errores, el CSV está listo para importar en App Pilar.
