# 🚀 Cómo crear el Ejecutable (.exe) para compartirlo

Tus compañeros no tienen por qué saber qué es Python ni qué es un entorno virtual (venv). Lo que ellos necesitan es un archivo **.exe** (en Windows) o **.app** (en Mac) al que hacerle doble clic, y que el programa se abra como cualquier otra aplicación.

¡La buena noticia es que **tu programa ya está preparado para hacer exactamente esto**!

## ¿Cómo funciona la "Magia"?
El archivo `desktop.py` que tienes en tu proyecto se encarga de coger todo tu código en Python, el servidor Flask, tu HTML, tu CSS y el navegador, y **meterlo todo dentro de un único archivo ejecutable**.

### Paso 1: Generar el archivo limpio
1. Como hicimos antes, ejecuta el script `scripts/create_clean_zip.py`.
2. Ese script genera el archivo `APP_EVALUAR_Limpio...zip`.
3. Pásate ese archivo ZIP limpio a un ordenador con **Windows** (o dáselo a un profesor que controle un poco más y tenga Windows).

### Paso 2: Convertirlo en un `.exe` (Solo se hace una vez)
En ese ordenador Windows, hay que compilar el programa para convertirlo en un `.exe`.

1. Descomprime el ZIP limpio en Windows.
2. Abre la terminal (`cmd`) o PowerShell en esa carpeta.
3. Instala los requisitos de Python (solo esta vez):
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller pywebview
   ```
4. Haz doble clic en el archivo que ya tienes creado llamado **`build_windows.bat`**.
   *(O escribe en la terminal: `build_windows.bat`)*

### Paso 3: ¡El Resultado Final!
El archivo `build_windows.bat` empezará a trabajar (puede tardar un par de minutos). Cuando termine, creará una nueva carpeta llamada **`dist`**.

Dentro de `dist/CuadernoDelTutor/` habrá un archivo llamado **`CuadernoDelTutor.exe`**.

**¡Ese es el archivo definitivo!**
Ese `.exe` ya tiene Python incrustado por dentro. Ya no hace falta `venv`, ni consola, ni nada. 
Puedes meter esa carpeta `CuadernoDelTutor` en un pendrive y pasársela a Pilar y a todo el claustro. Ellos solo tendrán que hacer doble clic en el `.exe` y la aplicación se abrirá en una ventana bonita de escritorio.

*(Lo mismo aplica para Mac usando el archivo `build_mac.sh` en un ordenador de Apple).*
