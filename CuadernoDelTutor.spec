# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('templates', 'templates'),
        ('schema.sql', '.'),
        ('version.py', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        # Swagger / marshmallow
        'flasgger',
        'marshmallow',
        # Flask-WTF y CSRF (importado directamente en app.py)
        'flask_wtf',
        'flask_wtf.csrf',
        'wtforms',
        'wtforms.validators',
        'wtforms.fields',
        'wtforms.fields.core',
        'wtforms.fields.html5',
        'wtforms.fields.simple',
        'wtforms.widgets',
        'wtforms.widgets.core',
        # python-dotenv
        'dotenv',
        # Werkzeug
        'werkzeug.security',
        'werkzeug.middleware.proxy_fix',
        'werkzeug.routing',
        # SQLite
        'sqlite3',
        # pkg_resources — falla silenciosa frecuente en Windows
        'pkg_resources.py2_compat',
        # Encodings — Windows puede necesitarlos
        'encodings.utf_8',
        'encodings.ascii',
        'encodings.latin_1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CuadernoDelTutor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # Desactivado: UPX provoca falsos positivos en antivirus
    console=True,        # console=True para la fase de pruebas — cambiar a False para versión Pilar
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,           # Desactivado: consistente con EXE
    upx_exclude=[],
    name='CuadernoDelTutor',
)
