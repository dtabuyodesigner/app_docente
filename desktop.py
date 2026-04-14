import os
import sys
import threading
import webbrowser
import argparse
import socket
from app import app
from utils.db import init_db_if_not_exists

DEFAULT_PORT = 5000

def configurar_autoarranque_windows():
    """Registra la aplicación en el arranque de Windows (solo cuando es el .exe compilado)."""
    if sys.platform != 'win32':
        return
    if not getattr(sys, 'frozen', False):
        return

    import winreg
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        exe_path = sys.executable
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "CuadernoDelTutor", 0, winreg.REG_SZ, exe_path)
    except Exception as e:
        print(f"Error al configurar autoarranque: {e}")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(preferred=DEFAULT_PORT):
    """Devuelve el puerto preferido si está libre, o uno aleatorio si no."""
    if not is_port_in_use(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def get_local_ip():
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

    # Si el servidor ya está corriendo en el puerto preferido, solo abrir el navegador
    if is_port_in_use(DEFAULT_PORT):
        url = f"http://127.0.0.1:{DEFAULT_PORT}"
        print(f"📡 Servidor ya en marcha en {url}")
        if not args.no_browser:
            webbrowser.open(url)
        return

    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        os.chdir(bundle_dir)

    init_db_if_not_exists()
    configurar_autoarranque_windows()

    port = find_free_port(DEFAULT_PORT)
    local_ip = get_local_ip()

    url_local = f"http://127.0.0.1:{port}"
    url_red = f"http://{local_ip}:{port}"

    print(f"📡 Servidor arrancado en {url_local}")
    print(f"📱 Acceso desde móvil/tablet: {url_red}")

    if not args.no_browser:
        threading.Timer(2.0, lambda: webbrowser.open(url_local)).start()

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
