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
    FOREIGN KEY(profesor_id) REFERENCES profesores(id)
);
CREATE TABLE areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE sda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    trimestre INTEGER NOT NULL,
    FOREIGN KEY (area_id) REFERENCES areas(id)
);
CREATE TABLE criterios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    area_id INTEGER NOT NULL,
    FOREIGN KEY (area_id) REFERENCES areas(id)
);
CREATE TABLE sda_criterios (
    sda_id INTEGER NOT NULL,
    criterio_id INTEGER NOT NULL,
    PRIMARY KEY (sda_id, criterio_id),
    FOREIGN KEY (sda_id) REFERENCES sda(id),
    FOREIGN KEY (criterio_id) REFERENCES criterios(id)
);
CREATE TABLE alumnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    no_comedor INTEGER DEFAULT 0,
    observacion_habitual TEXT,
    comedor_dias TEXT,
    foto TEXT,
    grupo_id INTEGER,
    FOREIGN KEY(grupo_id) REFERENCES grupos(id)
);
CREATE TABLE informe_grupo (
    trimestre INTEGER PRIMARY KEY,
    observaciones TEXT,
    propuestas_mejora TEXT
, conclusion TEXT);
CREATE TABLE programacion_diaria (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE NOT NULL, sda_id INTEGER, actividad TEXT NOT NULL, observaciones TEXT, tipo TEXT DEFAULT 'clase', color TEXT DEFAULT '#3788d8', FOREIGN KEY(sda_id) REFERENCES sda(id));
CREATE TABLE actividades_sda (id INTEGER PRIMARY KEY AUTOINCREMENT, sda_id INTEGER, nombre TEXT NOT NULL, sesiones INTEGER DEFAULT 1, descripcion TEXT, FOREIGN KEY(sda_id) REFERENCES sda(id));
CREATE TABLE rubricas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterio_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
    descriptor TEXT NOT NULL,
    UNIQUE(criterio_id, nivel),
    FOREIGN KEY(criterio_id) REFERENCES criterios(id)
);
CREATE TABLE horario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia INTEGER NOT NULL, -- 0=Mon, 4=Fri
    hora_inicio TEXT NOT NULL, -- HH:MM
    hora_fin TEXT NOT NULL, -- HH:MM
    asignatura TEXT NOT NULL,
    detalles TEXT
, tipo TEXT DEFAULT 'clase');
CREATE TABLE config (
    clave TEXT PRIMARY KEY,
    valor TEXT
);
CREATE TABLE menus_comedor (
    mes TEXT PRIMARY KEY, -- Format YYYY-MM
    imagen TEXT NOT NULL
);
CREATE TABLE config_ciclo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    asistentes_defecto TEXT
);
CREATE TABLE IF NOT EXISTS "asistencia" (
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
CREATE TABLE IF NOT EXISTS "evaluaciones" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                area_id INTEGER NOT NULL,
                trimestre INTEGER NOT NULL CHECK(trimestre BETWEEN 1 AND 3),
                sda_id INTEGER NOT NULL,
                criterio_id INTEGER NOT NULL,
                nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
                nota REAL NOT NULL,
                fecha DATE DEFAULT CURRENT_DATE,
                UNIQUE(alumno_id, criterio_id, sda_id, trimestre),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
                FOREIGN KEY(area_id) REFERENCES areas(id),
                FOREIGN KEY(sda_id) REFERENCES sda(id),
                FOREIGN KEY(criterio_id) REFERENCES criterios(id)
            );
CREATE TABLE IF NOT EXISTS gestor_tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    estado TEXT DEFAULT 'pendiente',
    prioridad TEXT DEFAULT 'media',
    fecha_limite DATE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "informe_individual" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                trimestre INTEGER NOT NULL,
                texto TEXT,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(alumno_id, trimestre),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            );
CREATE TABLE IF NOT EXISTS "encargados" (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                fecha DATE NOT NULL UNIQUE, 
                alumno_id INTEGER NOT NULL, 
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            );
CREATE TABLE IF NOT EXISTS "reuniones" (
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
CREATE TABLE IF NOT EXISTS "observaciones" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                texto TEXT NOT NULL, 
                area_id INTEGER REFERENCES areas(id),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            );
CREATE TABLE IF NOT EXISTS "ficha_alumno" (
                alumno_id INTEGER,
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
                PRIMARY KEY(alumno_id),
                FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
            );
CREATE TABLE IF NOT EXISTS "informe_observaciones" (
            alumno_id INTEGER NOT NULL,
            trimestre INTEGER NOT NULL,
            texto TEXT,
            PRIMARY KEY (alumno_id, trimestre),
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
        );
CREATE TABLE IF NOT EXISTS "usuarios" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'profesor',
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE IF NOT EXISTS "competencias_especificas" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            area_id INTEGER NOT NULL,
            FOREIGN KEY (area_id) REFERENCES areas(id)
        );
CREATE TABLE IF NOT EXISTS "sda_competencias" (
            sda_id INTEGER NOT NULL,
            competencia_id INTEGER NOT NULL,
            PRIMARY KEY (sda_id, competencia_id),
            FOREIGN KEY (sda_id) REFERENCES sda(id),
            FOREIGN KEY (competencia_id) REFERENCES competencias_especificas(id)
        );
