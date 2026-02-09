CREATE TABLE evaluaciones (
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

    FOREIGN KEY(alumno_id) REFERENCES alumnos(id),
    FOREIGN KEY(area_id) REFERENCES areas(id),
    FOREIGN KEY(sda_id) REFERENCES sda(id),
    FOREIGN KEY(criterio_id) REFERENCES criterios(id)
);
