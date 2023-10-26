# -*- mode: python ; coding: utf-8 -*-
import version

block_cipher = None


a = Analysis(
    ["interface.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("assets/img/*", "img"),
        ("assets/img/background/*", "assets/img/background"),
        ("assets/themes/*", "assets/themes"),
        ("assets/fonts/CircularStd-Black.otf", "."),
        ("assets/fonts/CircularStd-Bold.otf", "."),
        ("assets/config/cookies_spotify.txt", "."),
        ("main.qml", "."),
    ],
    hiddenimports=[],
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
    name="Lyrix",
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
    icon="img/logo.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f"Lyrix-{version.LYRIX_VERSION}",
)
