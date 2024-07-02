
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["crateDigAI_mac.py", "utils/playlist.py", "utils/inference_mac.py", "asset_downloader.py"],
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
    [],
    exclude_binaries=True,
    name="CrateDigAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
    icon="assets/logo.icns",  # Ensure you have an .icns file for macOS
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

app = BUNDLE(
    coll,
    name='CrateDigAI.app',
    icon='assets/logo.icns',  # Ensure you have an .icns file for macOS
    bundle_identifier='com.cratedig.CrateDig',  # Set your bundle identifier
    info_plist={
        'CFBundleExecutable': 'CrateDigAI',
        'CFBundleIdentifier': 'com.cratedig.CrateDig',
        'CFBundleName': 'CrateDigAI',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'CFBundlePackageType': 'APPL',
    },
)

