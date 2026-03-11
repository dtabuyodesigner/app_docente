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
1.  **Caché de Resultados**: Implementar un decorador simple de caché para endpoints de solo lectura (como listar criterios o áreas).
2.  **Validación con Marshmallow**: Empezar a migrar la validación manual de `criterios_api.py` a esquemas de Marshmallow.
3.  **Transacciones Atómicas**: Revisar `eventos.py` y `observaciones.py` para asegurar que todos los cambios usen `BEGIN/COMMIT` de forma consistente.

#### Documentación y UI
4.  **Swagger/OpenAPI**: Configurar `flask-smorest` o similar para documentar la API.
5.  **Interfaz UI**: Añadir campos de "Eventos" y "Observaciones" más detallados según el diseño de Manus.

#### Fase 2: Empaquetado
6.  **Instaladores**: Crear scripts para generar `.deb` (Linux), `.exe` (Windows) y `.dmg` (Mac).

---
> [!TIP]
> Para continuar, pídele al asistente: **"Lee el archivo de status del plan de Manus y sigue con el siguiente punto"**.
