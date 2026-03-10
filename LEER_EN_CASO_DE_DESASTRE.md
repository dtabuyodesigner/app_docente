# 🆘 ¿Qué hacer si se rompe tu ordenador? (Guía de Recuperación)

Si tu ordenador se estropea o cambias de equipo, **lo más importante que tienes que salvar son los archivos de esta carpeta**:
`~/.cuadernodeltutor/`

Ahí dentro están tu base de datos (`app_evaluar.db`) y todos tus Backups.

## 1. ¿Cómo entrar a la carpeta oculta para sacar los archivos?

Como la carpeta tiene un punto delante (`.cuadernodeltutor`), está oculta en Linux. 

**Opción A (La más fácil - Gráfica):**
1. Abre tu carpeta de Inicio (Home).
2. Pulsa en tu teclado **`Ctrl + H`**. Esto mostrará las carpetas ocultas.
3. Busca la carpeta `.cuadernodeltutor` y entra en ella.
4. Entra en `backups` y copia el archivo `.db` más reciente a un pendrive. (Si se salvó la base de datos entera, puedes copiar el archivo `app_evaluar.db`).

**Opción B (Desde la terminal):**
Para abrir la carpeta directamente, abre la terminal y pon:
```bash
xdg-open ~/.cuadernodeltutor
```

---

## 2. ¿Cómo restaurar los datos en el ordenador nuevo?

Imagina que ya tienes el Cuaderno instalado en tu ordenador nuevo y quieres meterle tus datos antiguos que salvaste en el pendrive. Sigue estos pasos:

1. Abre el programa vacío por primera vez en el ordenador nuevo para que cree la estructura de carpetas él solo. Ciérralo.
2. Coge el archivo de backup que sacaste del pendrive (ejemplo: `app_evaluar_backup_20260310...db`).
3. Renómbralo a **`app_evaluar.db`**.
4. Mételo dentro de la carpeta oculta del nuevo ordenador: `~/.cuadernodeltutor/`
 *(Sustituye el archivo en blanco que ya haya ahí por el tuyo).*
5. Abre el Cuaderno. ¡Estarán todos tus datos!

### 💡 Consejo Importante
Te recomiendo que de vez en cuando (una vez a la semana, por ejemplo), **descargues un backup manual** desde la pantalla "Configuración -> 💾 Backups" de la aplicación, y lo guardes en la nube (Drive, Dropbox) o en un pendrive físico. 

Tener el backup guardado en un pendrive te salva la vida si el disco duro de tu ordenador de trabajo se rompe hoy mismo.
