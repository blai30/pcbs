# Fuji75 PCB

Replacement hotswap PCB for the Sakura Workshop Fuji75, with per-key RGB and an RP2040. It fits the stock case, plate mount, daughterboard, and JST cable.

The layout is the stock Fuji75 hotswap layout except for the bottom right: 1u Alt, Fn, and Ctrl instead of 1.5u Alt and Ctrl (`reference/keyboard-layout.json`). The nav column is Insert, Delete, PgUp, and PgDn.

## KiCad project

Open `fuji75.kicad_pro` in KiCad 10.

- `fuji75.kicad_sch`: root sheet
- `fuji75-key-matrix.kicad_sch` and `fuji75-led-chain.kicad_sch`: generated
- `fuji75.kicad_pcb`: switches, diodes, LEDs, capacitors, stabilizers, outline, and flex cuts are generated
- `layout.json`: the layout with each key's matrix position as its top-left legend (`row,col`, VIA format). Opens in keyboard-layout-editor.com
- `fuji75.kicad_dru`: custom DRC rules for the socket pads at the board edge and the LED cutouts

The generator only runs during the key grid stage. It rebuilds the schematic and PCB from scratch, and it refuses to run once the PCB has parts it didn't make or any tracks.

Setup (once):

1. Run `"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user "kbplacer[schematic]==0.20"`.

Regenerate from the repo root:

1. Run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/generate.py` (add `--no-flex-cuts` for a solid board).

Footprints in `lib/` are copies from marbastlib (CERN-OHL-P, see `lib/marbastlib-LICENSE`) and KiCad's stock library. `LED_MX_6028R` has its pads renumbered to KiCad's SK6812 numbering (1 GND, 2 DIN, 3 VCC, 4 DOUT), which kbplacer expects.

The socket pads on Esc, \`, the nav column, and Right are trimmed to stop 0.3 mm inside the board edge (the socket tab hangs over the edge, like stock). Don't run "Update Footprints from Library" on those switches, it undoes the trim.

## Reference

Everything in `reference/` comes from measuring the stock PCB (Sakura Workshop doesn't share the design files):

- `fuji75_plate.dxf`: original plate model provided by Sakura Workshop (for reference)
- `measurements.md`: outline measurements, taken to the near edge of each switch's center hole (add 2 mm for the center)
- `measurement-guide.png`: diagram of where each measurement was taken, with the values
- `photos/`: both sides of the stock PCB, the case, and the daughterboard
- `j1-probe-guide.png`: J1 and the ATmega32U4's USB pins

## Stock board

- ATmega32U4 with a 16 MHz crystal
- 1.6 mm thick, no mounting holes (gasket mount, the PCB hangs from the plate)
- PCB-mount stabilizers
- One RGB LED under caps lock
- Outline edges sit half a key (9.525 mm) from the switch centers on the top, bottom, and F-row notch, and about 7.6 mm on the left and right
- Under the arrows, the right edge steps in about 4.6 mm, starting at the bottom of the End key

## USB connector

J1 is a JST SH 4-pin side-entry connector (SM04B-SRSS-TB) on the underside, near F1 and F2. It connects to the USB-C daughterboard with a 1:1 cable.

The pinout follows the Unified Daughterboard (the Fuji75 PCBs were sold as UDB compatible). Pin A is the one nearest the top edge of the board:

| Pin | Wire | Signal |
| --- | --- | --- |
| A | black | VBUS |
| B | red | D- |
| C | white | D+ |
| D | yellow | GND |

The wire colors don't follow USB conventions. Don't go by color.

The pinout wasn't checked with a multimeter. It comes from the UDB schematic, the [Fuji75 interest check](https://geekhack.org/index.php?topic=113840.0), and the traces between J1 and the 32U4 in `photos/IMG_5497.JPEG`. The new board adds reverse-polarity protection on VBUS in case it's wrong.

The daughterboard has its own fuse, ESD protection, CC resistors, and series resistors on D+ and D- (they look like 22 Ω).
