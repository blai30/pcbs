# Fuji75 RGB

QMK firmware for the Fuji75 RGB, a replacement hotswap PCB for the Sakura Workshop Fuji75 with an RP2040 and per-key RGB. The board design is in the parent folder.

- Keyboard maintainer: [blai30](https://github.com/blai30)
- Hardware supported: Fuji75 RGB v1.0.0

## Building

This folder is a QMK keyboard folder. Link it into a QMK checkout as `fuji75_rgb` once.

Windows (PowerShell):

```powershell
New-Item -ItemType Junction -Path "$HOME\qmk_firmware\keyboards\fuji75_rgb" -Target "<repo>\boards\fuji75-pcb\firmware"
```

macOS and Linux:

```bash
ln -s <repo>/boards/fuji75-pcb/firmware ~/qmk_firmware/keyboards/fuji75_rgb
```

Then build in QMK MSYS (or any shell with the `qmk` CLI):

```bash
qmk compile -kb fuji75_rgb -km default
```

The firmware file is `fuji75_rgb_default.uf2` in the QMK checkout's root.

## Flashing

Enter the bootloader one of these ways:

- Hold Esc while plugging in the cable
- Hold the boot button under the spacebar while plugging in the cable (pull the spacebar keycap first)
- Press Fn+Esc
- A board with blank flash starts in the bootloader on its own

The board shows up as a drive named `RPI-RP2`. Copy the `.uf2` file onto it. It restarts on its own.

## VIA

VIA doesn't know this board. Load `fuji75-via.json` once in VIA's Settings (turn on "Show Design tab"), then Design, then Load.

## Lock indicators

The board has no lock LEDs, so the key LEDs show them:

- Caps key: white while Caps Lock is on. While Fn is held it shows Num Lock instead
- F11: white while Scroll Lock is on

They only show while RGB is on (Fn+Insert).
