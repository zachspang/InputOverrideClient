# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec. Build with: python build.py
import sys

APP_NAME = "InputOverrideClient"

a = Analysis(
    ["main.py"],
    hiddenimports=[
        # pyserial loads URL handlers (hwgrep://) with importlib at runtime
        "serial.urlhandler.protocol_hwgrep",
        "pygame._sdl2.controller",
    ],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    # macOS: onedir build wrapped in a .app bundle
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        console=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name=APP_NAME)
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        bundle_identifier="com.zachspang.inputoverrideclient",
        info_plist={
            # Keep the 60 fps loop running at full speed while minimized/hidden
            "NSAppSleepDisabled": True,
            # Background controller input needs macOS 11.3+
            "LSMinimumSystemVersion": "11.3",
        },
    )
else:
    # Windows/Linux: single-file executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
        console=False,
    )
