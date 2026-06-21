# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Abilithic Recon (PyInstaller 6.x).
# Build:  pyinstaller abilithic-recon.spec --noconfirm --clean

datas = [
    ("abilithic_recon/data", "abilithic_recon/data"),
    ("abilithic_recon/i18n/locales", "abilithic_recon/i18n/locales"),
    ("assets", "assets"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["geoip2", "dns", "dns.resolver"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PyQt6"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AbilithicRecon",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                 # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/abilithic.ico",
)
