import os
import sys
import threading
import webbrowser
from app import app
from utils.db import init_db_if_not_exists

def find_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def main():
    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        os.chdir(bundle_dir)

    init_db_if_not_exists()

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    # 2 segundos: margen suficiente para que Flask arranque en Windows
    # (PyInstaller necesita más tiempo que en Linux para descomprimir _MEIPASS)
    threading.Timer(2.0, lambda: webbrowser.open(url)).start()

    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
