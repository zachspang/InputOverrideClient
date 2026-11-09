"""Build InputOverrideClient for the current OS.

    python build.py

PyInstaller can't cross-compile, so this only builds for the machine it runs on.
To build Windows, macOS and Linux at once, run the "Build" workflow from the
GitHub Actions tab (it runs this same script on each OS).

Output: dist/InputOverrideClient-<os>-<arch>.<zip|tar.gz>
"""
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

APP_NAME = "InputOverrideClient"
ROOT = Path(__file__).resolve().parent
WORK_DIR = ROOT / "build" / "pyinstaller-work"
BUILD_DIR = ROOT / "build" / "pyinstaller-dist"
DIST_DIR = ROOT / "dist"


def run(cmd, **kwargs):
    print(">", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT, **kwargs)


def target_name():
    os_name = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")
    machine = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(machine, machine)
    return f"{APP_NAME}-{os_name}-{arch}"


def built_executable():
    if sys.platform == "win32":
        return BUILD_DIR / f"{APP_NAME}.exe"
    if sys.platform == "darwin":
        return BUILD_DIR / f"{APP_NAME}.app" / "Contents" / "MacOS" / APP_NAME
    return BUILD_DIR / APP_NAME


def package(name):
    DIST_DIR.mkdir(exist_ok=True)
    if sys.platform == "win32":
        out = DIST_DIR / f"{name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(built_executable(), f"{APP_NAME}.exe")
    elif sys.platform == "darwin":
        # ditto keeps the .app bundle's symlinks and permissions intact
        out = DIST_DIR / f"{name}.zip"
        run(["ditto", "-c", "-k", "--keepParent", BUILD_DIR / f"{APP_NAME}.app", out])
    else:
        # tar keeps the executable bit
        out = DIST_DIR / f"{name}.tar.gz"
        with tarfile.open(out, "w:gz") as tf:
            tf.add(built_executable(), APP_NAME)
    return out


def main():
    run([sys.executable, "-m", "pip", "install", "-r", "requirements-build.txt"])

    for d in (WORK_DIR, BUILD_DIR, DIST_DIR):
        shutil.rmtree(d, ignore_errors=True)

    run([
        sys.executable, "-m", "PyInstaller", f"{APP_NAME}.spec",
        "--clean", "--noconfirm",
        "--workpath", WORK_DIR,
        "--distpath", BUILD_DIR,
    ])

    out = package(target_name())
    print(f"\nBuilt {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
