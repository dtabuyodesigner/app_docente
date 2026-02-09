-- Crear tabla para observaciones de informe por trimestre
CREATE TABLE IF NOT EXISTS informe_observaciones (
    alumno_id INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    texto TEXT,
    PRIMARY KEY (alumno_id, trimestre),
    FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
);
