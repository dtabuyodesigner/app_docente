CREATE TABLE profesores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nombre TEXT NOT NULL,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE grupos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    curso TEXT,
    profesor_id INTEGER,
    tipo_evaluacion TEXT DEFAULT 'primaria',
    etapa_id INTEGER,
    FOREIGN KEY(profesor_id) REFERENCES profesores(id),
    FOREIGN KEY(etapa_id) REFERENCES etapas(id)
);

CREATE TABLE etapas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);

-- Datos iniciales obligatorios
INSERT INTO etapas (id, nombre) VALUES (1, 'Infantil');
INSERT INTO etapas (id, nombre) VALUES (2, 'Primaria');
INSERT INTO etapas (id, nombre) VALUES (3, 'Secundaria');


CREATE TABLE areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    etapa_id INTEGER,
    es_oficial INTEGER DEFAULT 1,
    activa INTEGER DEFAULT 1,
    tipo_escala TEXT DEFAULT 'NUMERICA_1_4',
    modo_evaluacion TEXT DEFAULT 'POR_SA',
    FOREIGN KEY(etapa_id) REFERENCES etapas(id)
);

CREATE TABLE sda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    trimestre INTEGER NOT NULL,
    grupo_id INTEGER,
    codigo_sda TEXT,
    duracion_semanas INTEGER,
    FOREIGN KEY (area_id) REFERENCES areas(id),
    FOREIGN KEY (grupo_id) REFERENCES grupos(id)
);

CREATE TABLE criterios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    area_id INTEGER NOT NULL,
    activo INTEGER DEFAULT 1,
    oficial INTEGER DEFAULT 1,
    comentario_base TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES areas(id)
);

CREATE TABLE sda_criterios (
    sda_id INTEGER NOT NULL,
    criterio_id INTEGER NOT NULL,
    PRIMARY KEY (sda_id, criterio_id),
    FOREIGN KEY (sda_id) REFERENCES sda(id) ON DELETE CASCADE,
    FOREIGN KEY (criterio_id) REFERENCES criterios(id) ON DELETE CASCADE
);

CREATE TABLE alumnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    no_comedor INTEGER DEFAULT 0,
    observacion_habitual TEXT,
    comedor_dias TEXT,
    foto TEXT,
    grupo_id INTEGER,
    tiene_ayuda_material INTEGER DEFAULT 0,
    deleted_at DATETIME,
    FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

CREATE TABLE informe_grupo (
    trimestre INTEGER PRIMARY KEY,
    observaciones TEXT,
    propuestas_mejora TEXT,
    conclusion TEXT
);

CREATE TABLE programacion_diaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    fecha DATE NOT NULL, 
    sda_id INTEGER, 
    actividad_id INTEGER,
    numero_sesion INTEGER,
    descripcion TEXT,
    material TEXT,
    evaluable INTEGER DEFAULT 0,
    criterio_id INTEGER,
    tipo TEXT DEFAULT 'clase', 
    color TEXT DEFAULT '#3788d8', 
    FOREIGN KEY(sda_id) REFERENCES sda(id) ON DELETE SET NULL,
    FOREIGN KEY(actividad_id) REFERENCES actividades_sda(id) ON DELETE SET NULL,
    FOREIGN KEY(criterio_id) REFERENCES criterios(id) ON DELETE SET NULL
);

CREATE TABLE actividades_sda (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    sda_id INTEGER, 
    nombre TEXT NOT NULL, 
    sesiones INTEGER DEFAULT 1, 
    descripcion TEXT, 
    codigo_actividad TEXT,
    FOREIGN KEY(sda_id) REFERENCES sda(id) ON DELETE CASCADE
);

CREATE TABLE rubricas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterio_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
    descriptor TEXT NOT NULL,
    UNIQUE(criterio_id, nivel),
    FOREIGN KEY(criterio_id) REFERENCES criterios(id) ON DELETE CASCADE
);

CREATE TABLE horario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia INTEGER NOT NULL, -- 0=Mon, 4=Fri
    hora_inicio TEXT NOT NULL, -- HH:MM
    hora_fin TEXT NOT NULL, -- HH:MM
    asignatura TEXT NOT NULL,
    detalles TEXT,
    tipo TEXT DEFAULT 'clase'
);

CREATE TABLE config (
    clave TEXT PRIMARY KEY,
    valor TEXT
);

-- Configuración inicial por defecto
INSERT OR IGNORE INTO config (clave, valor) VALUES ('nombre_centro', '');
INSERT OR IGNORE INTO config (clave, valor) VALUES ('curso_escolar', '');
INSERT OR IGNORE INTO config (clave, valor) VALUES ('version', '1.1.0');


CREATE TABLE menus_comedor (
    mes TEXT PRIMARY KEY, -- Format YYYY-MM
    imagen TEXT NOT NULL
);

CREATE TABLE config_ciclo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    asistentes_defecto TEXT
);

CREATE TABLE asistencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    estado TEXT CHECK (estado IN ('presente', 'retraso', 'falta_justificada', 'falta_no_justificada')) NOT NULL,
    comedor INTEGER DEFAULT 1,
    observacion TEXT, 
    tipo_ausencia TEXT DEFAULT 'dia', 
    horas_ausencia TEXT,
    UNIQUE (alumno_id, fecha),
    FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
);

CREATE TABLE evaluaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    area_id INTEGER NOT NULL,
    trimestre INTEGER NOT NULL CHECK(trimestre BETWEEN 1 AND 3),
    sda_id INTEGER, -- Nullable for area-level evaluations (Infantil/Direct)
    criterio_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
    nota REAL NOT NULL,
    fecha DATE DEFAULT CURRENT_DATE,
    UNIQUE(alumno_id, criterio_id, sda_id, trimestre),
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    FOREIGN KEY(area_id) REFERENCES areas(id),
    FOREIGN KEY(sda_id) REFERENCES sda(id) ON DELETE SET NULL,
    FOREIGN KEY(criterio_id) REFERENCES criterios(id)
);

CREATE TABLE evaluaciones_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    area_id INTEGER NOT NULL,
    trimestre INTEGER NOT NULL CHECK(trimestre BETWEEN 1 AND 3),
    sda_id INTEGER,
    criterio_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
    nota REAL NOT NULL,
    fecha DATE DEFAULT CURRENT_DATE,
    comentario TEXT,
    UNIQUE(alumno_id, criterio_id, sda_id, trimestre, fecha),
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    FOREIGN KEY(area_id) REFERENCES areas(id),
    FOREIGN KEY(sda_id) REFERENCES sda(id) ON DELETE SET NULL,
    FOREIGN KEY(criterio_id) REFERENCES criterios(id)
);

CREATE TABLE evaluacion_criterios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    criterio_id INTEGER NOT NULL,
    periodo TEXT NOT NULL, -- T1, T2, T3
    nivel INTEGER NOT NULL,
    nota REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alumno_id, criterio_id, periodo),
    FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    FOREIGN KEY (criterio_id) REFERENCES criterios(id) ON DELETE CASCADE
);

CREATE TABLE gestor_tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    estado TEXT DEFAULT 'pendiente',
    prioridad TEXT DEFAULT 'media',
    fecha_limite DATE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE informe_individual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    texto TEXT,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alumno_id, trimestre),
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
);

CREATE TABLE encargados (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    fecha DATE NOT NULL UNIQUE, 
    alumno_id INTEGER NOT NULL, 
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
);

CREATE TABLE reuniones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER,
    fecha TEXT,
    asistentes TEXT,
    temas TEXT,
    acuerdos TEXT, 
    tipo TEXT DEFAULT 'PADRES', 
    ciclo_id INTEGER REFERENCES config_ciclo(id),
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
);

CREATE TABLE observaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    texto TEXT NOT NULL, 
    area_id INTEGER REFERENCES areas(id),
    FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
);

CREATE TABLE ficha_alumno (
    alumno_id INTEGER PRIMARY KEY,
    fecha_nacimiento TEXT,
    direccion TEXT,
    madre_nombre BLOB,
    madre_telefono BLOB,
    padre_nombre TEXT,
    padre_telefono TEXT,
    observaciones_generales TEXT, 
    personas_autorizadas TEXT, 
    madre_email TEXT, 
    padre_email TEXT,
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
);

CREATE TABLE criterios_periodo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterio_id INTEGER NOT NULL,
    grupo_id INTEGER NOT NULL,
    periodo TEXT NOT NULL, -- T1, T2, T3
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (criterio_id) REFERENCES criterios(id) ON DELETE CASCADE,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    UNIQUE(criterio_id, grupo_id, periodo)
);

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'profesor',
    pregunta_seguridad TEXT,
    respuesta_seguridad_hash TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE competencias_especificas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    area_id INTEGER NOT NULL,
    FOREIGN KEY (area_id) REFERENCES areas(id)
);

CREATE TABLE sda_competencias (
    sda_id INTEGER NOT NULL,
    competencia_id INTEGER NOT NULL,
    PRIMARY KEY (sda_id, competencia_id),
    FOREIGN KEY (sda_id) REFERENCES sda(id) ON DELETE CASCADE,
    FOREIGN KEY (competencia_id) REFERENCES competencias_especificas(id) ON DELETE CASCADE
);

CREATE TABLE material_alumnado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo_id INTEGER NOT NULL,
    categoria TEXT NOT NULL, -- 'AYUDA' or 'TODO'
    unidades INTEGER DEFAULT 1,
    material TEXT NOT NULL,
    FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

CREATE TABLE material_info (
    grupo_id INTEGER PRIMARY KEY,
    centro TEXT,
    curso_escolar TEXT,
    nivel_curso TEXT,
    observaciones TEXT,
    FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

CREATE TABLE material_entregado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    entregado INTEGER DEFAULT 0, -- 0: No, 1: Sí
    fecha_entrega DATETIME,
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    FOREIGN KEY(material_id) REFERENCES material_alumnado(id) ON DELETE CASCADE,
    UNIQUE(alumno_id, material_id)
);

-- INDEXES FOR PERFORMANCE
CREATE INDEX idx_eval_alumno_trim ON evaluaciones (alumno_id, trimestre);
CREATE INDEX idx_eval_area ON evaluaciones (area_id);
CREATE INDEX idx_eval_sda ON evaluaciones (sda_id);
CREATE INDEX idx_eval_criterio ON evaluaciones (criterio_id);
CREATE INDEX idx_eval_crit_alumno ON evaluacion_criterios (alumno_id, periodo);
CREATE INDEX idx_sda_area ON sda (area_id);
CREATE INDEX idx_sda_grupo ON sda (grupo_id);
CREATE INDEX idx_criterios_area ON criterios (area_id);
CREATE INDEX idx_asistencia_alumno_fecha ON asistencia (alumno_id, fecha);
CREATE INDEX idx_alumno_grupo ON alumnos (grupo_id);
CREATE INDEX idx_crit_per_periodo ON criterios_periodo (periodo);

-- LIBRARY MODULE TABLES
CREATE TABLE IF NOT EXISTS libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    isbn TEXT,
    editorial TEXT,
    año_publicacion INTEGER,
    nivel_lectura TEXT,
    genero TEXT,
    cantidad_disponible INTEGER DEFAULT 1,
    cantidad_total INTEGER DEFAULT 1,
    descripcion TEXT,
    portada TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS prestamos_libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    libro_id INTEGER NOT NULL,
    fecha_prestamo DATE NOT NULL,
    fecha_devolucion DATE,
    estado TEXT DEFAULT 'activo', 
    observaciones TEXT,
    dias_retraso INTEGER DEFAULT 0,
    FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    FOREIGN KEY (libro_id) REFERENCES libros(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generos_lectura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS niveles_lectura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT
);
