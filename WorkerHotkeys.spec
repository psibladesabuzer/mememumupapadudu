# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\assets', 'assets'), ('C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\ahk', 'ahk'), ('C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\assets', 'assets'), ('C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\ahk', 'ahk'), ('C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\app\\ui\\style.qss', 'app/ui'), ('C:\\Users\\qinqva\\PycharmProjects\\main_workable_app\\app\\ui\\style_light.qss', 'app/ui')],
    hiddenimports=[],
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
    name='WorkerHotkeys',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    upx=True,
    upx_exclude=[],
    name='WorkerHotkeys',
)
