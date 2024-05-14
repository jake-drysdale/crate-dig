# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["crateDigAI.py", "utils/playlist.py", "utils/inference.py", "asset_downloader.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
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
    # comment out these 3 lines to make it a directory based app instead
    # a.binaries,
    # a.zipfiles,
    # a.datas,
    [],
    exclude_binaries=True,
    name="CrateDigAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
    icon="assets/logo.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CrateDigAI",
)
