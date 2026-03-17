# Registro de Progreso: Plan de Manus

Este archivo sirve como memoria para continuar con las tareas de mejora del proyecto `APP_EVALUAR` siguiendo el plan de Manus.

## 🏁 Estado Actual (2026-03-11)

### Fase 1: Mejoras de Escritorio
- [x] **Infraestructura de Tests**: Creada carpeta `tests/`, `conftest.py` y `test_basic.py`. Entorno `pytest` configurado y validado.
- [x] **Logging de Auditoría**: Implementado `audit_log` en `utils/security.py` e integrado en `criterios_api.py`. Se registra en `audit.log`.
- [x] **Filtros y Navegación**: Corregido el filtro "Etapa" y el botón "Volver" dinámico en `evaluacion.html`.
- [x] **Optimización BD**: Los índices de rendimiento ya están presentes en `schema.sql`.

### ⏳ Pendiente (Próximos Pasos)

#### Críticos e Importantísimos (Tareas Cortas < 10min)
1.  [x] **Caché de Resultados**: Implementado via decorador `simple_cache` en `utils/cache.py` para endpoints de lectura (`criterios` y `areas`).
2.  [x] **Validación con Marshmallow**: Migrada la validación manual de `criterios_api.py` a esquemas de Marshmallow.
3.  [x] **Transacciones Atómicas**: Agrupados los cambios en `eventos.py` y `observaciones.py` usando bloques estructurados robustos con `BEGIN` y `COMMIT` / `ROLLBACK`.

#### Documentación y UI
4.  [x] **Swagger/OpenAPI**: Configurar `flask-smorest` o similar para documentar la API. Usado `flasgger` por facilidad.
5.  [x] **Interfaz UI**: Añadir campos de "Eventos" y "Observaciones" más detallados según el diseño de Manus. Aprobado y añadido tags en `#diario.html`.

#### Fase 2: Empaquetado y v1.1
6.  [x] **Instaladores**: Crear scripts para generar `.deb` (Linux), [x] `.exe` (Windows completado por usuario), y `.dmg` (Mac).
7.  [x] **Autoupdater**: Sistema para detectar nuevas versiones en GitHub Releases e integrado en Configuración.
8.  [x] **Restauración Externa (v1.1)**: Botón para subir y restaurar archivos `.db` externos implementado en `configuracion.html` y `admin.py`.
9.  [x] **Versión**: Actualizado a `v1.1.0`.

---
> [!TIP]
> Para continuar, pídele al asistente: **"Lee el archivo de status del plan de Manus y sigue con el siguiente punto"**.
