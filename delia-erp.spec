# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)
backend_dir = project_root / "backend"
web_dir = project_root / "frontend" / "dist" / "delia-erp" / "browser"

if not (web_dir / "index.html").is_file():
    raise SystemExit("Build the Angular frontend before running PyInstaller.")

hidden_imports = []
for package in ("uvicorn", "openpyxl", "xlrd", "xlsxwriter"):
    hidden_imports.extend(collect_submodules(package))
hidden_imports.extend(["multipart", "python_multipart"])
tray_backend = {
    "darwin": "pystray._darwin",
    "win32": "pystray._win32",
}.get(sys.platform, "pystray._xorg")
hidden_imports.append(tray_backend)

a = Analysis(
    [str(backend_dir / "desktop.py")],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[(str(web_dir), "web")],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "httpx"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeliaERP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "frontend" / "public" / "favicon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DeliaERP",
)
