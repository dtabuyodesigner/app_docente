# Guía: Configurar Google Calendar API

Sigue estos pasos para obtener las credenciales necesarias:

## Paso 1: Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Inicia sesión con tu cuenta de Gmail
3. Haz clic en el selector de proyectos (arriba a la izquierda)
4. Clic en "NUEVO PROYECTO"
5. Nombre del proyecto: `Cuaderno del Tutor` (o el que prefieras)
6. Clic en "CREAR"

## Paso 2: Habilitar Google Calendar API

1. En el menú lateral, ve a **APIs y servicios** → **Biblioteca**
2. Busca "Google Calendar API"
3. Haz clic en "Google Calendar API"
4. Clic en **HABILITAR**

## Paso 3: Crear Credenciales OAuth 2.0

1. Ve a **APIs y servicios** → **Credenciales**
2. Clic en **+ CREAR CREDENCIALES** → **ID de cliente de OAuth**
3. Si te pide configurar la pantalla de consentimiento:
   - Tipo de usuario: **Externo**
   - Nombre de la aplicación: `Cuaderno del Tutor`
   - Correo de asistencia: tu email
   - Clic en **GUARDAR Y CONTINUAR** (puedes dejar el resto en blanco)
4. Vuelve a **Credenciales** → **+ CREAR CREDENCIALES** → **ID de cliente de OAuth**
5. Tipo de aplicación: **Aplicación web**
6. Nombre: `Cuaderno del Tutor - Local`
7. **URIs de redireccionamiento autorizados**: Añade:
   ```
   http://127.0.0.1:5000/oauth2callback
   ```
8. Clic en **CREAR**

## Paso 4: Descargar Credenciales

1. Aparecerá un popup con tu **ID de cliente** y **Secreto del cliente**
2. Clic en **DESCARGAR JSON**
3. Guarda el archivo como `credentials.json` en la carpeta:
   ```
   /home/danito73/Documentos/APP_EVALUAR/credentials.json
   ```

## ¡Listo!

Una vez tengas el archivo `credentials.json`, avísame y continuaré con la implementación del código.
