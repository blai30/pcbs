# Fuji75 PCB

Replacement hotswap PCB for the Sakura Workshop Fuji75, with per-key RGB and an RP2040. It fits the stock case, plate mount, daughterboard, and JST cable.

The layout is the stock Fuji75 hotswap layout with two changes (`reference/keyboard-layout.json`): stepped caps lock, and 1u Alt, Fn, and Ctrl in the bottom right instead of 1.5u Alt and Ctrl. The nav column is Insert, Delete, PgUp, and PgDn.

## KiCad project

Open `fuji75.kicad_pro` in KiCad 10.

- `fuji75.kicad_sch`: root sheet
- `fuji75-key-matrix.kicad_sch` and `fuji75-led-chain.kicad_sch`: generated
- `fuji75-controller.kicad_sch`: USB in, power, the LED power switch, RP2040, flash, clock, boot and reset buttons, SWD pads, and the LED level shifter. Edited by hand
- `fuji75.kicad_pcb`: switches, LEDs, stabilizers, outline, and flex cuts came from the generator. Diodes, LED capacitors, the controller, and all routing were placed and drawn by one-off scripts after that. The board file is the source now
- `layout.json`: the layout with each key's matrix position as its top-left legend (`row,col`, VIA format). Opens in keyboard-layout-editor.com
- `fuji75.kicad_dru`: custom DRC rules for the socket pads at the board edge and the LED cutouts

White solder mask, black silkscreen, and ENIG finish, set in the board stackup (Board Setup, Physical Stackup). Renders only use the colors with `kicad-cli pcb render --use-board-stackup-colors`.

`scripts/generate.py` built the key grid. It's locked now: it rebuilds the schematic and PCB from scratch, so it refuses to run once the PCB has parts it didn't make (the controller) or any tracks. Its `check_holes_inside` and `check_min_web` still work on their own (DRC doesn't check holes crossing an edge or board material thinner than 1 mm).

To run it again on a board without the controller, install kbplacer once with `"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user "kbplacer[schematic]==0.20"`, then run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/generate.py` from the repo root (add `--no-flex-cuts` for a solid board).

Footprints in `lib/` are copies from marbastlib (CERN-OHL-P, see `lib/marbastlib-LICENSE`) and KiCad's stock library. The RP2040's QFN-56 pads are 0.17 mm wide instead of the datasheet's 0.20 mm. White solder mask needs at least 0.22 mm between pads (PCBWay), and 0.17 mm leaves 0.23 mm. `LED_MX_6028R` has its pads renumbered to KiCad's SK6812 numbering (1 GND, 2 DIN, 3 VCC, 4 DOUT), which kbplacer expects.

The socket pads on Esc, \`, the nav column, and Right are trimmed to stop 0.3 mm inside the board edge (the socket tab hangs over the edge, like stock). The arrow keys' LED cutouts open into the bottom edge as notches (a closed cutout would leave a 0.09 mm strip, too thin to make). Don't run "Update Footprints from Library" on those switches or the arrow LEDs (LED73 to LED75), it undoes the trim and the notches.

## Controller

The circuit follows Raspberry Pi's minimal RP2040 design (12 MHz crystal, W25Q16JV flash, AP2112K 3.3 V regulator). USB comes in through J1 in the stock spot, then a USBLC6-2SC6 ESD chip and an AO3401A MOSFET that blocks reversed power. The ESD chip's VBUS pin is on the MOSFET's output side (on the input side, a reversed cable shorts through it). R1 and R2 are the RP2040's 27 Ω USB series resistors, next to the chip like in Raspberry Pi's design.

The ESD chip and the MOSFET sit on the bottom behind J1 (the side away from the opening). D+ and D- cross under J1 on the top layer. Only flat tracks sit in front of J1's opening, and the cable plug slides in straight. The RP2040, flash, regulator, and level shifter sit under the spacebar, where there's room for them (the strip by J1 is too narrow on 2 layers). USB runs about 19 cm from J1 to the chip. That's fine at full speed (12 Mbps).

GPIO pin map:

| GPIO | Signal |
| --- | --- |
| 0 | Board ID, tied to GND (v1.1.0) |
| 1 | ROW5 |
| 2 | LED data (through the 74AHCT1G125 to 5 V) |
| 3 | ROW4 |
| 4 to 7 | COL3, COL2, COL1, COL0 |
| 8 to 11 | ROW3, ROW2, ROW1, ROW0 |
| 13 | `LED_FAULT`, U6's fault output (v1.1.0) |
| 14 | `LED_EN`, U6's enable (v1.1.0) |
| 18 to 28 | COL14 down to COL4 |
| 29 | `LED_SENSE`, the LED voltage through a divider (v1.1.0) |

GPIO 12 and 15 to 17 are unused. On v1.0.0, GPIO 0, 13, 14, and 29 are unconnected.

Parts sit on both sides. The crystal, the 12 RP2040 decoupling capacitors, R1 and R2, and the sense divider are on the top side right above the chip (under the spacebar), and so are the boot and reset buttons.

To enter the bootloader, pull the spacebar keycap, hold the boot button through the plate window right of the spacebar switch (a toothpick or tweezers work), and plug in the cable. A board with blank flash goes to the bootloader on its own. The reset button (SW101) sits right of the boot button in the same window. Holding boot and pressing reset enters the bootloader without unplugging. RUN has no external pull-up (the RP2040's internal one holds it high). Keycaps can't reach the buttons, even multi-stem spacebars (they sit below the plate). The plate needs an opening over the buttons. The FR4 plate has its own window for them, and both plungers sit inside the stock plate's spacebar cutouts.

SWD pads TP1 to TP5 sit on the bottom about 9 mm south of the RP2040, 2.54 mm apart, for clips or a probe. Left to right, labeled on the silkscreen: 3V3, GND, CLK (SWCLK), DIO (SWDIO), RUN.

## Power

VBUS goes through Q1 (reverse protection) to `VCC`. The controller gets its own 0.3 mm feed from Q1. The LEDs sit behind U6, a TPS2553 load switch with soft-start, enable, and fault output. R5 (21.5 kΩ) sets its current limit to about 1.2 A, above the firmware's LED budget. C119 (1 µF) is on its input and C120 (10 µF) on its output.

U6's output is `LED_5V`. All 82 LEDs and their 100 nF caps are on it. The trunk down the left edge is 1.0 mm (0.5 mm for a short span by a peg hole), and the 0.2 mm row lines branch off it.

R6 (15 kΩ) and R7 (10 kΩ) divide `LED_5V` down to 0.4 for GPIO 29 (ADC). The tap is on the row-4 lane near the controller, far from the feed at the top left. It sees close to the worst drop on the board.

The budget comes from the JST SH connector, rated 1 A per contact (one VBUS pin, one GND pin). The firmware estimates each frame's current and scales the frame down when it's over budget:

- v1.0.0: fixed 800 mA. 950 mA sagged the LED voltage under 4.5 V and turned white orange
- v1.1.0: adaptive, 300 to 950 mA. It lowers the budget when `LED_5V` sags and raises it back slowly

One firmware build runs on both. It reads GPIO 0 at startup (tied to GND on v1.1.0, pulled up internally on v1.0.0) to tell them apart.

## Firmware

QMK with VIA, in `firmware/`. See `firmware/readme.md` for building, flashing, and loading the VIA definition.

- 1000 Hz polling and NKRO
- RGB brightness goes to 255. A current limit in the RGB driver scales each frame to the LED budget (see [Power](#power))
- One build for v1.0.0 and v1.1.0. Each revision has its own VIA definition (caps lock differs)
- USB ID `0x1209`/`0x0001` is pid.codes' test PID until this board gets its own

## Routing

Each layer has one job. Rows and columns never cross on the same layer:

- Top: the columns, straight down between the switches. They cross a flex cut only at a bridge or in the 10 mm strips at the ends
- Bottom: one row line and one LED power line straight through each row of keys, and the LED data chain hopping LED to LED. The LEDs in rows 0, 2, and 4 are turned around, and the chain snakes left-right-left down the board
- Between rows 4 and 5, the columns gather into two buses into the chip
- Ground fill on both sides, stitched together with vias
- No bottom copper within 2.5 mm of a stabilizer screw hole, where the screw heads sit (keepouts in the stabilizer footprints)
- Flex cuts stop at least 4 mm from any stabilizer hole (the stabilizer housing never sits across a cut)

Tracks are 0.2 mm, including the LED power line through each row. The 5 V trunk is 1.0 mm (0.5 mm by one peg hole). The controller's 5 V feed and the 3.3 V lines are 0.3 to 0.5 mm. The USBLC6-2SC6 and button footprints mark the pads that are joined inside the part (jumper pad groups). DRC treats them as connected.

## Plate

`plate/fuji75-plate.kicad_pcb` is an FR4 switch plate for this layout, ordered as a PCB. It shares the PCB's coordinates and lines up with it when overlaid.

`scripts/plate.py` builds it from the stock plate DXF:

- Stock outline and T-shaped gasket tabs
- Stock 14 mm switch cutouts wherever they match a switch on the PCB (70 of 82)
- Stock backspace cutout, copied to Enter and left shift
- A plain 14 mm spacebar switch cutout, and a separate window over the boot and reset buttons, with at least 3 mm of plate between the two
- New cutouts for the rest from the PCB footprints: stepped caps lock, backslash, the bottom row, and the spacebar stabilizers. The multi-layout stock cutouts are gone
- Spacebar stabilizer cutouts the size of the backspace's stabilizer notches (the stock ones were 1.5 mm taller)
- No flex cuts. JLCPCB rejected slots closer than 3 mm to another cutout or the edge, and there's no room for that between keys. Every cutout is at least 3 mm from the next. The only narrower spots are 1.1 to 1.6 mm between the bottom row and the bottom edge, set by the stock outline

`--slots` adds the stock plate's 2 mm vertical slots between keys (plus new ones between the bottom-right 1u keys). `--row-cuts` adds 1 mm cuts between rows with staggered 3 mm bridges (the printed plate's pattern in the 3d-prints repo), stopping 1.5 mm from every cutout and slot. Both leave 1.5 to 2 mm webs, for a fab that allows them.

It also writes `plate/fuji75-plate-foam.dxf` and a 1:1 vector `plate/fuji75-plate-foam.pdf` (for shops that ask for a PDF), the plate foam that sits between the plate and the PCB (3 to 3.5 mm PORON or PE, the gap is about 3.4 mm under the 1.6 mm plate). It follows the PCB outline 0.5 mm in, with:

- A 15 mm hole for each switch (14 mm below the plate, plus room for the clips)
- A hole over each stabilizer housing, clearing both of its PCB holes by 0.75 mm
- A channel for each stabilizer wire between its housings, from 3 mm inside the big PCB holes to past their outer edge (the wire runs under the plate). The spacebar's channel cuts off the foam under the spacebar, so that's two loose pieces that drop in on their own
- One region around the controller parts on top of the PCB under the spacebar, and one around the boot and reset buttons
- Holes closer than 1.9 mm to each other or to the edge merged into one region (thinner foam tears), so the top and side rows open into the edge. Loose islands that leaves (one, by left Ctrl and Win) are cut out too

The script checks that every switch and both buttons sit fully inside a cutout, that the plate is still one piece, and that nothing leaves less than 1 mm of material. Install its libraries once with `"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user ezdxf shapely`, then run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/plate.py` from the repo root. Run `fab.py` after it.

## Fab

Run `"C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/fab.py` from the repo root. It writes `build/fab/`:

- `fuji75-gerbers.zip`: Gerbers and drill files
- `fuji75-bom.csv`: BOM with manufacturer and LCSC part numbers (every symbol has `MPN` and `LCSC` fields)
- `fuji75-bom-jlcpcb.csv`: the same BOM in JLCPCB's format (Comment, Designator, Footprint, LCSC Part #)
- `fuji75-cpl.csv`: placement for both sides
- `fuji75-cpl-jlcpcb.csv`: the same placement with JLCPCB's rotation offsets
- `fuji75-plate-gerbers.zip`: the plate's Gerbers (top copper, top mask, and outline only, for a 1-layer order)

[limitations.md](limitations.md) lists the design's limitations (most of them from the stock outline and case) and possible improvements, including ways to cut the manufacturing cost.

[pcbway-order.md](pcbway-order.md) has every PCBWay form setting, the notes to paste, and what to check in the rotation photos. In short: 2 layers, 1.6 mm, 1 oz copper, ENIG, white mask, black silkscreen, 5 boards with 2 assembled on both sides (turnkey). Stabilizers are left out.

[jlcpcb-order.md](jlcpcb-order.md) has the same for JLCPCB.

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

The pinout comes from the UDB schematic, the [Fuji75 interest check](https://geekhack.org/index.php?topic=113840.0), and the traces between J1 and the 32U4 in `photos/IMG_5497.JPEG`. It wasn't checked with a multimeter, but the v1.0.0 board works with the stock daughterboard and cable.

The daughterboard has its own fuse, ESD protection, CC resistors, and series resistors on D+ and D- (they look like 22 Ω). With R1 and R2 (27 Ω) that makes about 49 Ω per line. That's slightly over spec, but fine at full speed. v1.0.0 has 0 Ω in R1 and R2.

On v1.1.0, U2 sits behind J1 and only flat tracks run in front of the opening. The connector is rated 1 A per contact, and it carries all the power through one VBUS pin and one GND pin. That sets the LED budget (see [Power](#power)).

## Revisions

The version is printed on the underside, under the spacebar. Photos of the assembled v1.0.0 boards are in `photos/v1.0.0/`.

- v1.1.0: order this one
  - The ESD chip (U2) moved behind J1. Only flat tracks sit in front of J1's opening, and the cable plug goes in straight
  - R1 and R2 are real 27 Ω resistors next to the RP2040 (0 Ω next to J1 on v1.0.0)
  - LED power switch (U6, TPS2553) with a 1.2 A limit. The LEDs are on their own `LED_5V` net, and the RP2040 can turn it off
  - LED voltage sense on GPIO 29. The firmware adapts the LED budget between 300 and 950 mA (fixed 800 mA on v1.0.0)
  - Board ID strap on GPIO 0 (tied to GND), for the firmware
  - The 5 V trunk down the left edge is 1.0 mm (0.5 mm on v1.0.0)
  - Stepped caps lock. The switch moved 4.76 mm left, under the raised 1.25u part of a stepped keycap. Regular 1.75u caps lock keycaps don't fit anymore
  - The boot button moved 3 mm right. A reset button (SW101) sits next to it, and both share one plate window. The FR4 plate's spacebar switch cutout is closed on all four sides
  - SWD pads on the bottom (3V3, GND, SWCLK, SWDIO, RUN)
  - Six fiducials, three per side
  - The v1.1.0 FR4 plate doesn't fit v1.0.0 boards (caps lock moved). The stock plate fits both
  - Its VIA definition is `firmware/fuji75-via.json`. v1.0.0 uses `firmware/fuji75-via-v1.0.0.json`
- v1.0.0: the first boards made. They work, but U2 sits about 2 mm in front of J1's opening. The cable plug only goes in at an angle, it's very tight to seat, and the wires arch over U2. Caps lock takes a regular 1.75u keycap

## License

The board is under CERN-OHL-P-2.0 (repo root `LICENSE`). The footprints in `lib/` are marbastlib's, under the same license. The firmware in `firmware/` is under GPL-2.0-or-later.
