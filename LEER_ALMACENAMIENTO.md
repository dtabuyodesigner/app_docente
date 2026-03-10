# 📁 Guía de Almacenamiento y Compartición del Cuaderno del Docente

Esta guía te explica de forma muy sencilla dónde están tus datos ahora mismo y cómo debes compartir la aplicación con otras personas sin enviarles tus cosas.

## 1. El Archivo que debes compartir (El ZIP "Limpio")

Cuando quieras mandar el Cuaderno a Pilar o a cualquier otro compañero, **solo debes enviar este archivo**:

- **Nombre:** `APP_EVALUAR_Limpio_YYYYMMDD.zip` (por ejemplo, `APP_EVALUAR_Limpio_20260310.zip`)
- **Ruta:** `/home/danito73/Documentos/APP_EVALUAR/APP_EVALUAR_Limpio_20260310.zip`

**¿Qué contiene este archivo?**
Contiene todo el código necesario para que la aplicación funcione en su ordenador, pero está completamente vacío de datos. Cuando ellos lo abran, el programa creará una base de datos nueva y les pedirá configurar su propio usuario y contraseña de acceso.

---

## 2. Dónde están TUS datos personales (Seguros y Ocultos)

Tu base de datos (con todos tus alumnos, notas, programaciones y configuraciones) **sigue existiendo y funcionando exactamente igual**, pero ya no vive en la carpeta principal del código.

La hemos movido a una carpeta propia de tu sistema Linux, que está diseñada para guardar configuraciones de usuario de forma invisible y permanente:

- **Ruta Oculta:** `/home/danito73/.cuadernodeltutor/app_evaluar.db`

*(El punto `.` delante de `cuadernodeltutor` significa que es una carpeta oculta. Tu sistema operativo no la borra por accidente y no aparece a simple vista).*

### ¿Dónde se guardan los datos nuevos que metes ahora?
Todo lo que estás guardando ahora (nuevas faltas de asistencia, nuevas notas, etc.) **se guarda automáticamente en esta misma ubicación segura**:
`~/.cuadernodeltutor/app_evaluar.db`

### ¿Dónde se guardan tus Copias de Seguridad (Backups)?
Al igual que tu base de datos central, los backups diarios y manuales que hagas se guardan en esta carpeta secreta junto a la BD:
`/home/danito73/.cuadernodeltutor/backups/`

---

## 💡 Resumen
1. **Tu aplicación sigue intacta:** Entra desde el navegador como siempre.
2. **Tus datos están protegidos:** Están en `/home/danito73/.cuadernodeltutor/`.
3. **Compartir:** Pasa el archivo `APP_EVALUAR_Limpio...zip` (que está en tu carpeta de Documentos) a tus compañeros. ¡Tus datos NO viajan en ese ZIP!
