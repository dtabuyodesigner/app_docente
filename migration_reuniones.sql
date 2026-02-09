CREATE TABLE IF NOT EXISTS reuniones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER,
    fecha TEXT,
    asistentes TEXT,
    temas TEXT,
    acuerdos TEXT,
    FOREIGN KEY(alumno_id) REFERENCES alumnos(id)
);
