CREATE TABLE IF NOT EXISTS informe_individual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    texto TEXT,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alumno_id, trimestre),
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id)
);
