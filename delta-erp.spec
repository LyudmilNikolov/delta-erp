# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)
backend_dir = project_root / "backend"
web_dir = project_root / "frontend" / "dist" / "delta-erp" / "browser"

if not (web_dir / "index.html").is_file():
    raise SystemExit("Build the Angular frontend before running PyInstaller.")

hidden_imports = []
for package in ("uvicorn", "openpyxl", "xlrd", "xlsxwriter"):
    hidden_imports.extend(collect_submodules(package))
hidden_imports.extend(["multipart", "python_multipart"])

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
    name="DeltaERP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    name="DeltaERP",
)
