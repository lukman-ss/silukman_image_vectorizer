# -*- mode: python ; coding: utf-8 -*-
import os
import re
import sys

block_cipher = None

with open(os.path.join('app', 'core', 'constants.py'), 'r', encoding='utf-8') as constants_file:
    constants_text = constants_file.read()
version_match = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', constants_text, re.MULTILINE)
APP_VERSION = version_match.group(1) if version_match else '1.0.0'

# Dynamically detect application icon based on platform
icon_file = None
resources_path = os.path.join('app', 'resources')
if os.path.exists(resources_path):
    for f in os.listdir(resources_path):
        name, ext = os.path.splitext(f)
        if name.lower() == 'icon':
            if sys.platform == 'darwin' and ext.lower() == '.icns':
                icon_file = os.path.join(resources_path, f)
                break
            elif sys.platform == 'win32' and ext.lower() == '.ico':
                icon_file = os.path.join(resources_path, f)
                break
            elif sys.platform.startswith('linux') and ext.lower() == '.png':
                icon_file = os.path.join(resources_path, f)
                break

spec_datas = []
if os.path.exists('app/resources'):
    spec_datas.append(('app/resources', 'app/resources'))
if os.path.exists('docs'):
    spec_datas.append(('docs', 'docs'))
if os.path.exists('LICENSE'):
    spec_datas.append(('LICENSE', '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=spec_datas,
    hiddenimports=[
        'PIL',
        'cv2',
        'numpy',
        'vtracer',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'app.core',
        'app.services',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Image Vectorizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
    disable_windowed_traceback=False,
    argv_emulation=True if sys.platform == 'darwin' else False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Image Vectorizer',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Image Vectorizer.app',
        icon=icon_file,
        bundle_identifier='com.mycompany.imagevectorizer',
        info_plist={
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': True,
        },
    )
