# Nomenclatura de Criterios de Evaluación

## Formato

```
{n_sda}_{area_abbrev}_{CE}_{C}
```

- `{n_sda}` — número de la SDA (ej. `6`, `7`, `8`…)
- `{area_abbrev}` — abreviatura del área (ver tablas abajo)
- `{CE}` — competencia específica (ej. `CE2`)
- `{C}` — criterio (ej. `C3`)

### Ejemplos

```
6_CA_CE2_C3      → SDA 6, Crecimiento en Armonía, CE2 criterio 3
6_DEE_CE3_C5     → SDA 6, Descubrimiento y Exploración del Entorno, CE3 criterio 5
6_CRR_CE1_C4     → SDA 6, Comunicación y Representación de la Realidad, CE1 criterio 4
7_MAT_CE2_C1     → SDA 7, Matemáticas, CE2 criterio 1
```

---

## Abreviaturas por etapa

### Infantil (5 años)

| Abreviatura | Área completa |
|-------------|---------------|
| `DEE`       | Descubrimiento y Exploración del Entorno |
| `CRR`       | Comunicación y Representación de la Realidad |
| `CA`        | Crecimiento en Armonía |

### Primaria

| Abreviatura | Área completa |
|-------------|---------------|
| `LEN`       | Lengua Castellana y Literatura |
| `MAT`       | Matemáticas |
| `CON`       | Conocimiento del Medio Natural, Social y Cultural |
| `ING`       | Lengua Extranjera (Inglés) |
| `EF`        | Educación Física |
| `ART`       | Educación Artística (Plástica y Música) |
| `REL`       | Religión / Valores Sociales y Cívicos |

> Si el centro usa otras áreas o denominaciones distintas, añadir aquí la abreviatura acordada.

---

## Instrucción para prompt de IA (generación de CSV SDA)

Incluir este bloque en cualquier prompt que pida a una IA generar el CSV de una SDA:

---

### BLOQUE A COPIAR EN EL PROMPT DE IA

```
FORMATO DEL CAMPO Criterio_Codigo:
El código de cada criterio debe seguir el patrón: {n_sda}_{area_abbrev}_{CE}_{C}

Donde:
- {n_sda}  = número de la SDA (el dígito del campo SDA_ID, p.ej. SDA6_DEE → 6)
- {area_abbrev} = abreviatura del área según esta tabla:
    Infantil:
      DEE  = Descubrimiento y Exploración del Entorno
      CRR  = Comunicación y Representación de la Realidad
      CA   = Crecimiento en Armonía
    Primaria:
      LEN  = Lengua Castellana y Literatura
      MAT  = Matemáticas
      CON  = Conocimiento del Medio Natural, Social y Cultural
      ING  = Lengua Extranjera (Inglés)
      EF   = Educación Física
      ART  = Educación Artística
      REL  = Religión / Valores Sociales y Cívicos
- {CE}  = competencia específica (p.ej. CE2)
- {C}   = criterio (p.ej. C3)

Ejemplos correctos:
  6_CA_CE2_C3     (SDA 6, Crecimiento en Armonía, CE2 criterio 3)
  6_DEE_CE3_C5    (SDA 6, Descubrimiento del Entorno, CE3 criterio 5)
  7_CRR_CE1_C4    (SDA 7, Comunicación y Representación, CE1 criterio 4)
  8_MAT_CE2_C1    (SDA 8, Matemáticas, CE2 criterio 1)

Solo pongas Criterio_Codigo en la primera fila de cada criterio de la SDA.
Las filas de sesiones/actividades sin criterio nuevo dejan la columna vacía.

La columna Criterios_Vinculados (criterios relacionados, separados por coma)
también debe usar el mismo formato: 6_DEE_CE2_C3,6_DEE_CE1_C4
NUNCA uses el formato antiguo CE2_C3 sin prefijo — sin el número de SDA y
el área es imposible saber a qué pertenece el criterio.
```

---

## Por qué importa el prefijo

Un código como `CE2_C5` es ambiguo: puede existir en DEE, CRR, CA, MAT o LEN.
`6_DEE_CE2_C5` es inequívoco: SDA 6, área DEE, CE2 criterio 5.

Si en la base de datos ya hay criterios importados con el formato antiguo (sin prefijo),
deben borrarse desde **Gestión → Criterios** y reimportar con los CSV corregidos.

---
