# Fuji75 PCB

Replacement hotswap PCB for the Sakura Workshop Fuji75, with per-key RGB and an RP2040. It fits the stock case, plate mount, daughterboard, and JST cable.

The layout is the stock Fuji75 hotswap layout except for the bottom right: 1u Alt, Fn, and Ctrl instead of 1.5u Alt and Ctrl (`reference/keyboard-layout.json`). The nav column is Insert, Delete, PgUp, and PgDn.

## KiCad project

Open `fuji75.kicad_pro` in KiCad 10.

- `fuji75.kicad_sch`: root sheet
- `fuji75-key-matrix.kicad_sch` and `fuji75-led-chain.kicad_sch`: generated
- `fuji75-controller.kicad_sch`: USB in, power, RP2040, flash, clock, boot button, and the LED level shifter. Edited by hand
- `fuji75.kicad_pcb`: switches, LEDs, stabilizers, outline, and flex cuts came from the generator. Diodes, LED capacitors, the controller, and all routing were placed and drawn by one-off scripts after that. The board file is the source now
- `layout.json`: the layout with each key's matrix position as its top-left legend (`row,col`, VIA format). Opens in keyboard-layout-editor.com
- `fuji75.kicad_dru`: custom DRC rules for the socket pads at the board edge and the LED cutouts

White solder mask, black silkscreen, and ENIG finish, set in the board stackup (Board Setup, Physical Stackup). Renders only use the colors with `kicad-cli pcb render --use-board-stackup-colors`.

`scripts/generate.py` built the key grid. It's locked now: it rebuilds the schematic and PCB from scratch, so it refuses to run once the PCB has parts it didn't make (the controller) or any tracks. Its `check_holes_inside` and `check_min_web` still work on their own (DRC doesn't check holes crossing an edge or board material thinner than 1 mm).

To run it again on a board without the controller, install kbplacer once with `"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user "kbplacer[schematic]==0.20"`, then run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/generate.py` from the repo root (add `--no-flex-cuts` for a solid board).

Footprints in `lib/` are copies from marbastlib (CERN-OHL-P, see `lib/marbastlib-LICENSE`) and KiCad's stock library. The RP2040's QFN-56 pads are 0.17 mm wide instead of the datasheet's 0.20 mm. White solder mask needs at least 0.22 mm between pads (PCBWay), and 0.17 mm leaves 0.23 mm. `LED_MX_6028R` has its pads renumbered to KiCad's SK6812 numbering (1 GND, 2 DIN, 3 VCC, 4 DOUT), which kbplacer expects.

The socket pads on Esc, \`, the nav column, and Right are trimmed to stop 0.3 mm inside the board edge (the socket tab hangs over the edge, like stock). The arrow keys' LED cutouts open into the bottom edge as notches (a closed cutout would leave a 0.09 mm strip, too thin to make). Don't run "Update Footprints from Library" on those switches or the arrow LEDs (LED73 to LED75), it undoes the trim and the notches.

## Controller

The circuit follows Raspberry Pi's minimal RP2040 design (12 MHz crystal, W25Q16JV flash, AP2112K 3.3 V regulator). USB comes in through J1 in the stock spot, then a USBLC6-2SC6 ESD chip and an AO3401A MOSFET that blocks reversed power. The ESD chip's VBUS pin is on the MOSFET's output side (on the input side, a reversed cable shorts through it). The daughterboard already has 22 Ω resistors on D+ and D-, so the RP2040's own 27 Ω pair are 0 Ω placeholders (R1, R2).

The ESD chip, R1, R2, and the MOSFET sit next to J1. The RP2040, flash, regulator, and level shifter sit under the spacebar, where there's room for them (the strip by J1 is too narrow on 2 layers). USB runs about 19 cm from J1 to the chip. That's fine at full speed (12 Mbps).

GPIO pin map:

| GPIO | Signal |
| --- | --- |
| 1 | ROW5 |
| 2 | LED data (through the 74AHCT1G125 to 5 V) |
| 3 | ROW4 |
| 4 to 7 | COL3, COL2, COL1, COL0 |
| 8 to 11 | ROW3, ROW2, ROW1, ROW0 |
| 18 to 28 | COL14 down to COL4 |

GPIO 0, 12 to 17, and 29 are unused.

Parts sit on both sides. The crystal and the 12 RP2040 decoupling capacitors are on the top side right above the chip (under the spacebar), and so is the boot button.

To enter the bootloader, pull the spacebar keycap, hold the button in the window right of the spacebar switch, and plug in the cable. A board with blank flash goes to the bootloader on its own. Keycaps can't reach the button, even multi-stem spacebars (it sits below the plate). The printed plate has to keep the stock plate's wide spacebar cutout.

## Firmware

QMK with VIA, in `firmware/`. See `firmware/readme.md` for building, flashing, and loading the VIA definition.

- 1000 Hz polling and NKRO
- RGB brightness is capped at 36 of 255 (about 14%). All 82 LEDs at full white would draw about 3 A, and the cap keeps that worst case near 420 mA, under USB's 500 mA
- USB ID `0x1209`/`0x0001` is pid.codes' test PID until this board gets its own

## Routing

Each layer has one job. Rows and columns never cross on the same layer:

- Top: the columns, straight down between the switches. They cross a flex cut only at a bridge or in the 10 mm strips at the ends
- Bottom: one row line and one LED power line straight through each row of keys, and the LED data chain hopping LED to LED. The LEDs in rows 0, 2, and 4 are turned around, and the chain snakes left-right-left down the board
- Between rows 4 and 5, the columns gather into two buses into the chip
- Ground fill on both sides, stitched together with vias
- No bottom copper within 2.5 mm of a stabilizer screw hole, where the screw heads sit (keepouts in the stabilizer footprints)
- Flex cuts stop at least 4 mm from any stabilizer hole (the stabilizer housing never sits across a cut)

Tracks are 0.2 mm, including the LED power line through each row. The 5 V trunk and the 3.3 V lines are 0.3 to 0.5 mm. The USBLC6-2SC6 and boot button footprints mark the pads that are joined inside the part (jumper pad groups). DRC treats them as connected.

## Fab

Run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/fab.py` from the repo root. It writes `build/fab/`:

- `fuji75-gerbers.zip`: Gerbers and drill files
- `fuji75-bom.csv`: BOM with manufacturer and LCSC part numbers (every symbol has `MPN` and `LCSC` fields)
- `fuji75-cpl.csv`: placement for both sides

[pcbway-order.md](pcbway-order.md) has every PCBWay form setting, the notes to paste, and what to check in the rotation photos. In short: 2 layers, 1.6 mm, 1 oz copper, ENIG, white mask, black silkscreen, 5 boards with 2 assembled on both sides (turnkey). Stabilizers are left out.

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

## License

The board is under CERN-OHL-P-2.0 (repo root `LICENSE`). The footprints in `lib/` are marbastlib's, under the same license. The firmware in `firmware/` is under GPL-2.0-or-later.
