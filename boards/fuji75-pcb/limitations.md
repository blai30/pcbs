# Limitations

Most of these come from keeping the stock Fuji75 outline, case, and daughterboard. The rest are fab and assembly rules that came up during the PCBWay order.

## Board edges and assembly

- Assembly machines grip the board by two opposite edges and need about 5 mm clear of parts along them. The outline sits about 7.6 mm from the left and right switch centers. That puts the hotswap sockets right at the edge (the pads stop 0.3 mm inside it, and the socket tab hangs over)
- PCBWay adds breakaway rails for assembly and cuts them off afterward. That's a tab-routing fee (about $25 on this order)
- The arrow cluster steps the bottom-right edge in. The arrow LED cutouts are notches open to the edge (a closed cutout would leave a 0.09 mm strip)
- Fiducials sit inside the board, three per side (1 mm copper dot, 2 mm mask opening). v1.0.0 has none, and PCBWay added them on the rails
- Parts on both sides. The RP2040's decoupling caps, the crystal, R1 and R2, the sense divider, and the boot and reset buttons are on the top. That makes it a two-sided assembly (two stencils, two setups)

## Fab

- White solder mask needs at least 0.22 mm between IC pads to print the mask strip between them. The RP2040's datasheet pads leave 0.20 mm at 0.4 mm pitch. Its pads are narrowed to 0.17 mm (0.23 mm gaps)
- The hotswap socket footprints have their origin at the switch center, about 3.8 mm off the socket body. `fab.py` moves each socket's placement point to the midpoint of its two pin holes
- The LED edge clearance rule in `fuji75.kicad_dru` only applies to pads. Scoped to the whole footprint, it also covers the footprint's Edge.Cuts lines and lets the ground fill come within 0.25 mm of the LED cutouts
- PCBWay's form quote leaves out the internal cutouts, the rails, and the reviewed assembly cost. The reviewed price is well above it

## Case

- The daughterboard and J1 stay in the stock spot by F1 and F2. The strip there is too narrow for the controller on 2 layers. The RP2040 sits under the spacebar and USB runs about 19 cm across the board (fine at full speed)
- No mounting holes (gasket mount, the PCB hangs from the plate). Stabilizer screw heads sit on the bottom, and the stabilizer footprints keep copper away from the screw holes
- The boot and reset buttons are only reachable with the spacebar keycap pulled

## Power

- 82 RGB LEDs at full white draw about 3 A. J1 is a JST SH connector rated 1 A per contact, with one VBUS pin and one GND pin. That sets the budget at 1 A total, about 950 mA for the LEDs
- The firmware estimates each frame's current and scales it down to the budget. v1.0.0 uses a fixed 800 mA (950 mA sagged the LED voltage and turned white orange). v1.1.0 senses the LED voltage and adapts between 300 and 950 mA
- White on all 82 LEDs tops out at about a quarter of full brightness (62 of 255 at 800 mA). Full brightness needs a daughterboard with more power pins and the CC lines (to ask the host for 3 A), and a new cable
- Most of the voltage drop is likely off the board (USB cable, daughterboard fuse, JST cable). Wider row lines wouldn't fix it
- The 0.2 mm row power lines carry about 0.25 A each at the 1 A budget. The 1.0 mm trunk down the left edge carries all of it. U6 limits the LED power to about 1.2 A if the firmware gets it wrong (v1.1.0 only)

## Possible improvements

Cost:

- Move the 22 top-side parts to the bottom next to the RP2040 for single-sided assembly (one stencil, one setup). The bottom around the chip is crowded on 2 layers, so it may need a re-route
- Leave the hotswap sockets out of assembly and solder them by hand. They're 82 of the 366 parts, with large pads that are easy to solder with an iron
- Green solder mask. The RP2040 keeps its datasheet pads, and green is the fastest and cheapest option at most fabs
- HASL instead of ENIG. Cheaper, but less flat for the QFN and the fine-pitch parts
- JLCPCB instead of PCBWay. Usually cheaper for small assembly runs, and every part here has an LCSC number. Some parts count as extended parts with a fee of about $3 each
- An outline with 5 mm of clear board along both long edges, so no rails or tab routing. That needs a different case

Design:

- Hotswap socket footprints with their origin at the socket center, so `fab.py` doesn't have to move them
- A boot button reachable without pulling a keycap (the firmware has a key combo, Fn+Esc)
- A custom USB-C daughterboard with more power pins and the CC lines, for full white at about 3 A
