# InputOverrideClient

Reads a game controller on your computer and sends its button state over USB serial to a DSpico, so the controller can play the DS.

Works on Windows, macOS, and Linux.

> [!WARNING]
> This has not been thoroughly tested in most games. **Back up your save files** before using this and often while using it.

## Requirements

Your DSpico must be running these forks of the firmware and pico-loader, built from their `feature/usb-input-hook` branches.

- [dspico-firmware (feature/usb-input-hook)](https://github.com/zachspang/dspico-firmware/tree/feature/usb-input-hook)
- [pico-loader (feature/usb-input-hook)](https://github.com/zachspang/pico-loader/tree/feature/usb-input-hook)

[This guide](https://github.com/LNH-team/dspico/blob/develop/GUIDE.md) explains how to setup your dspico. In step 5 clone [this](https://github.com/zachspang/dspico-firmware) instead.
Skip step 7 and download this release of [pico-loader](https://github.com/zachspang/pico-loader/releases/latest). Place the 5 files from the pico-loader zip into a folder named _pico at the root of your SD.

## Running it

Download the file for your OS from the Releases page.

### Windows
Unzip `InputOverrideClient-windows-x64.zip` and run `InputOverrideClient.exe`.

### macOS
Unzip `InputOverrideClient-macos-arm64.zip` (Apple Silicon) or `InputOverrideClient-macos-x64.zip` (Intel) and move `InputOverrideClient.app` wherever you like.

### Linux
Extract the archive and run the binary:

```bash
tar xzf InputOverrideClient-linux-x64.tar.gz
./InputOverrideClient
```

**One-time setup:** Linux only lets members of the `dialout` group use serial devices. Add yourself once, then log out and back in:

```bash
sudo usermod -aG dialout $USER
```

On Arch-based distros the group is `uucp` instead of `dialout`.

## Controller mapping

Buttons are mapped by position, so it works the same with Xbox, PlayStation, and Switch controllers on every OS.

| Controller (Xbox name) | DS button |
|---|---|
| A (bottom) | B |
| B (right) | A |
| X (left) | Y |
| Y (top) | X |
| LB | L |
| RB | R |
| Back / View | Select |
| Start / Menu | Start |
| D-pad | D-pad |

With more than one controller connected, use the **Next controller** button to choose which one is sent to the DS.

## Building

```bash
python -m venv .venv
```

Activate the venv, then:

```bash
python build.py
```

This installs the build dependencies, builds the app, and writes `dist/InputOverrideClient-<os>-<arch>.zip`.
