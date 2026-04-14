import os
import sys
import threading
import webbrowser
import argparse
from app import app
from utils.db import init_db_if_not_exists

def configurar_autoarranque_windows():
    """Registra la aplicación en el arranque de Windows (solo cuando es el .exe compilado)."""
    if sys.platform != 'win32':
        return
    if not getattr(sys, 'frozen', False):
        return

    import winreg
    try:
        # HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        exe_path = sys.executable

        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "CuadernoDelTutor", 0, winreg.REG_SZ, exe_path)
    except Exception as e:
        # Fallo silencioso en producción para no molestar al usuario
        print(f"Error al configurar autoarranque: {e}")

def find_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def get_local_ip():
    """Obtiene la IP local para acceso desde otros dispositivos de la red."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-browser', action='store_true', help='No abrir el navegador al arrancar')
    args = parser.parse_args()

    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        os.chdir(bundle_dir)

    init_db_if_not_exists()

    # Configurar autoarranque (solo Windows EXE)
    configurar_autoarranque_windows()

    port = find_free_port()
    local_ip = get_local_ip()

    url_local = f"http://127.0.0.1:{port}"
    url_red = f"http://{local_ip}:{port}"

    print(f"📡 Servidor arrancado en {url_local}")
    print(f"📱 Acceso desde móvil/tablet: {url_red}")

    if not args.no_browser:
        threading.Timer(2.0, lambda: webbrowser.open(url_local)).start()

    # Escuchar en todas las interfaces (0.0.0.0) para acceso desde red local
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
