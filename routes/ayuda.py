import os
from flask import Blueprint, send_from_directory, session, redirect

ayuda_bp = Blueprint('ayuda', __name__)

@ayuda_bp.route('/ayuda')
def ayuda():
    if not session.get('logged_in'):
        return redirect('/login')
    # Use the directory of this file to find the static folder path
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'), 'ayuda.html')
