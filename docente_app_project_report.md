# Portfolio del Proyecto: Cuaderno del Tutor (APP_EVALUAR)

Este documento proporciona una visión completa del estado actual del proyecto **Cuaderno del Tutor**, una aplicación de escritorio diseñada para la gestión docente integral. Está estructurado para facilitar la validación técnica y funcional por parte de terceros (Manus/AI).

---

## 1. Visión General y Arquitectura

**Cuaderno del Tutor** es una solución offline-first para docentes que centraliza la gestión de alumnos, asistencia, evaluación y programación.

- **Frontend**: Single Page Application (SPA) construida con HTML5, CSS3 (Vanilla) y JavaScript (Vanilla). Se prioriza la agilidad y la compatibilidad sin dependencias pesadas.
- **Backend**: Micro-servidor en **Python 3 con Flask**, utilizando una arquitectura modular basada en Blueprints.
- **Base de Datos**: **SQLite 3**, optimizada para el uso local con manejo de integridad y backups automáticos.
- **Seguridad**: Implementación de seguridad por capas (CSRF, Hashing, Log de Seguridad).
- **Integraciones**: Sincronización bidireccional con **Google Calendar API (v3)**.

---

## 2. Módulos Funcionales

### 📊 Módulo de Evaluación (Core)
El corazón del cuaderno, recientemente rediseñado para soportar la diversidad pedagógica:
- **Modos de Evaluación**: 
  - Por Situaciones de Aprendizaje (SDA).
  - Por Criterios Directos (Área/Materia).
  - Soporte para Criterios Extra ad-hoc.
- **Escalas Dinámicas**:
  - **Numérica (1-4)**: Base estándar para Primaria/Secundaria.
  - **Infantil (NI, EP, C)**: Interfaz simplificada (Necesita Mejorar, En Progreso, Conseguido) con mapeo automático a valores numéricos internos para el cálculo de medias.
- **Gestión de Criterios**: Pestaña integrada dentro de Evaluación para un acceso rápido.
  - **Importación CSV Robusta**: Sistema de carga masiva con validación estricta de cabeceras, detección de errores fila a fila y reporte descargable de fallos.
  - **Lógica de Upsert**: Actualización automática de criterios existentes basada en Código + Etapa + Área para evitar duplicidad.

### 👥 Gestión de Alumnos y Grupos
- **Fichas Individuales**: Datos personales, fotos de perfil y seguimiento.
- **Carga Masiva**: Importación de alumnado vía CSV con validación de campos.
- **Gestión de Grupos**: Filtrado global de la aplicación por grupo de alumnos.

### 📋 Asistencia y Diario de Clase
- **Control Diario**: Faltas, retrasos y faltas justificadas.
- **Comedor**: Registro rápido de comensales.
- **Calendario**: Vista de agenda con integración de "Sesiones de Actividad" y eventos de Google Calendar.

### 📓 Reuniones y Tutoría
- **Actas de Padres**: Registro individualizado de tutorías.
- **Actas de Ciclo**: Coordinación entre docentes.
- **Exportación PDF**: Generación de documentos listos para imprimir y firmar.

### 📜 Generación de Informes
- **Individuales**: PDF con resumen de progreso, observaciones y gráficas de rendimiento generadas dinámicamente (`matplotlib`).
- **Grupales**: Exportación a Excel y PDF con estadísticas de promoción y asistencia.

---

## 3. Seguridad y Robustez (Blindaje Técnico)

Se han implementado medidas de nivel empresarial para asegurar la integridad de los datos:
- **Protección CSRF**: Todas las peticiones POST/PUT/DELETE están protegidas contra ataques de falsificación de petición en sitios cruzados.
- **Autenticación Segura**: Uso de `werkzeug.security` para el hasheo de contraseñas y gestión de sesiones.
- **Sistema de Backup Automático**: Cada inicio de la aplicación genera una copia de seguridad con rotación, asegurando que el docente nunca pierda información por fallos de hardware.
- **Logs de Seguridad**: Registro detallado de acciones sensibles (login, importaciones, cambios de contraseña) en `security.log`.
- **Validación Estricta**: Los endpoints de API validan roles (`admin` vs `profesor`) y la integridad de los datos de entrada (especialmente en importaciones CSV).

---

## 4. Estructura de Datos Clave (Schema)

- `usuarios`: Gestión de accesos y roles.
- `alumnos`: Datos maestros del alumnado.
- `criterios`: Repositorio oficial de criterios de evaluación (unificados por `codigo`, `etapa` y `area_id`).
- `seguimiento_sda`: Registro histórico de calificaciones.
- `gestor_tareas`: Tareas pendientes del docente con niveles de prioridad y alertas de vencimiento.

---

## 5. Próximos Pasos y Escalabilidad
- Integración de escalas específicas para Secundaria (LOMLOE).
- Mejora de la interfaz de informes con plantillas personalizables.
- Preparación para empaquetado como ejecutable nativo mediante `PyInstaller` o `pywebview`.

---
*Generado automáticamente para revisión técnica.*
