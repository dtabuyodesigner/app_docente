import os
import sys
import webview
from app import app
from utils.db import init_db_if_not_exists

def main():
    # Make sure we are in the correct directory (helps PyInstaller)
    if getattr(sys, 'frozen', False):
        # The application is frozen
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        os.chdir(bundle_dir)
        
    # Ensure DB is created if it doesn't exist
    init_db_if_not_exists()
    
    # Create a desktop window embedding the Flask application
    # pywebview automatically hosts the Flask app on a random local port
    window = webview.create_window(
        title='Cuaderno del Tutor', 
        url=app, 
        width=1280, 
        height=800, 
        min_size=(1024, 600),
        confirm_close=True
    )
    
    # Start the application loop
    webview.start(
        debug=False,
        http_server=True # Ensure a reliable web server backend for Flask
    )

if __name__ == '__main__':
    main()
