# Fuji75 PCB

Replacement hotswap PCB for the Sakura Workshop Fuji75, with per-key RGB and an RP2040. It fits the stock case, plate mount, daughterboard, and JST cable.

The layout is the stock Fuji75 hotswap layout except for the bottom right: 1u Alt, Fn, and Ctrl instead of 1.5u Alt and Ctrl (`reference/keyboard-layout.json`). The nav column is Insert, Delete, PgUp, and PgDn.

## KiCad project

Open `fuji75.kicad_pro` in KiCad 10.

- `fuji75.kicad_sch`: root sheet
- `fuji75-key-matrix.kicad_sch` and `fuji75-led-chain.kicad_sch`: generated
- `fuji75-controller.kicad_sch`: USB in, power, RP2040, flash, clock, boot button, and the LED level shifter. Edited by hand
- `fuji75.kicad_pcb`: switches, diodes, LEDs, capacitors, stabilizers, outline, and flex cuts are generated. The controller parts are placed by hand
- `layout.json`: the layout with each key's matrix position as its top-left legend (`row,col`, VIA format). Opens in keyboard-layout-editor.com
- `fuji75.kicad_dru`: custom DRC rules for the socket pads at the board edge and the LED cutouts

`scripts/generate.py` built the key grid. It's locked now: it rebuilds the schematic and PCB from scratch, so it refuses to run once the PCB has parts it didn't make (the controller) or any tracks. Its `check_holes_inside` and `check_min_web` still work on their own (DRC doesn't check holes crossing an edge or board material thinner than 1 mm).

To run it again on a board without the controller, install kbplacer once with `"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user "kbplacer[schematic]==0.20"`, then run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/generate.py` from the repo root (add `--no-flex-cuts` for a solid board).

Footprints in `lib/` are copies from marbastlib (CERN-OHL-P, see `lib/marbastlib-LICENSE`) and KiCad's stock library. `LED_MX_6028R` has its pads renumbered to KiCad's SK6812 numbering (1 GND, 2 DIN, 3 VCC, 4 DOUT), which kbplacer expects.

The socket pads on Esc, \`, the nav column, and Right are trimmed to stop 0.3 mm inside the board edge (the socket tab hangs over the edge, like stock). The arrow keys' LED cutouts open into the bottom edge as notches (a closed cutout would leave a 0.09 mm strip, too thin to make). Don't run "Update Footprints from Library" on those switches or the arrow LEDs (LED73 to LED75), it undoes the trim and the notches.

## Controller

The circuit follows Raspberry Pi's minimal RP2040 design (12 MHz crystal, W25Q16JV flash, AP2112K 3.3 V regulator). USB comes in through J1 in the stock spot, then a USBLC6-2SC6 ESD chip and an AO3401A MOSFET that blocks reversed power. The daughterboard already has 22 Ω resistors on D+ and D-, so the RP2040's own 27 Ω pair are 0 Ω placeholders (R1, R2).

GPIO pin map (first pass, routing may still swap pins):

| GPIO | Signal |
| --- | --- |
| 0 to 14 | COL0 to COL14 |
| 15 to 20 | ROW0 to ROW5 |
| 22 | LED data (through the 74AHCT1G125 to 5 V) |

Parts sit on both sides. The 12 RP2040 decoupling capacitors are on the top side right above the chip (under the plate), and so is the boot button.

To enter the bootloader, pull the spacebar keycap, hold the button in the window right of the spacebar switch, and plug in the cable. A board with blank flash goes to the bootloader on its own. Keycaps can't reach the button, even multi-stem spacebars (it sits below the plate). The printed plate has to keep the stock plate's wide spacebar cutout.

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
