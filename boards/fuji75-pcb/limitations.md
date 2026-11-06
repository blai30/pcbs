# Limitations

Most of these come from keeping the stock Fuji75 outline, case, and daughterboard. The rest are fab and assembly rules that came up during the PCBWay order.

## Board edges and assembly

- Assembly machines grip the board by two opposite edges and need about 5 mm clear of parts along them. The outline sits about 7.6 mm from the left and right switch centers. That puts the hotswap sockets right at the edge (the pads stop 0.3 mm inside it, and the socket tab hangs over)
- PCBWay adds breakaway rails for assembly and cuts them off afterward. That's a tab-routing fee (about $25 on this order)
- The arrow cluster steps the bottom-right edge in. The arrow LED cutouts are notches open to the edge (a closed cutout would leave a 0.09 mm strip)
- No fiducials. PCBWay adds them on the rails
- Parts on both sides. The RP2040's decoupling caps, the crystal, and the boot button are on the top, so it's a two-sided assembly (two stencils, two setups)

## Fab

- White solder mask needs at least 0.22 mm between IC pads to print the mask strip between them. The RP2040's datasheet pads leave 0.20 mm at 0.4 mm pitch. Its pads are narrowed to 0.17 mm (0.23 mm gaps)
- The hotswap socket footprints have their origin at the switch center, about 3.8 mm off the socket body. `fab.py` moves each socket's placement point to the midpoint of its two pin holes
- The LED edge clearance rule in `fuji75.kicad_dru` only applies to pads. Scoped to the whole footprint, it also covers the footprint's Edge.Cuts lines and lets the ground fill come within 0.25 mm of the LED cutouts
- PCBWay's form quote leaves out the internal cutouts, the rails, and the reviewed assembly cost. The reviewed price is well above it

## Case

- The daughterboard and J1 stay in the stock spot by F1 and F2. The strip there is too narrow for the controller on 2 layers. The RP2040 sits under the spacebar and USB runs about 19 cm across the board (fine at full speed)
- The J1 pinout comes from research, not a meter. Reverse-polarity protection only covers power
- No mounting holes (gasket mount, the PCB hangs from the plate). Stabilizer screw heads sit on the bottom, and the stabilizer footprints keep copper away from the screw holes
- The boot button is only reachable with the spacebar keycap pulled

## Power

- 82 RGB LEDs at full white draw about 3 A, and USB gives 500 mA. The firmware caps brightness at 36 of 255. The 0.2 mm LED power lines depend on that cap
- One 100 nF cap per LED plus the 10 µF regulator input cap adds up to about 18 µF on VBUS. USB's limit is 10 µF. Most hosts don't care

## Possible improvements

Cost:

- Move the 17 top-side parts to the bottom next to the RP2040 for single-sided assembly (one stencil, one setup). The bottom around the chip is crowded on 2 layers, so it may need a re-route
- Leave the hotswap sockets out of assembly and solder them by hand. They're 82 of the 359 parts, with large pads that are easy to solder with an iron
- Green solder mask. The RP2040 keeps its datasheet pads, and green is the fastest and cheapest option at most fabs
- HASL instead of ENIG. Cheaper, but less flat for the QFN and the fine-pitch parts
- JLCPCB instead of PCBWay. Usually cheaper for small assembly runs, and every part here has an LCSC number. Some parts count as extended parts with a fee of about $3 each
- An outline with 5 mm of clear board along both long edges, so no rails or tab routing. That needs a different case

Design:

- Fiducials, 3 per assembled side (1 mm copper dot, 2 mm mask opening)
- Hotswap socket footprints with their origin at the socket center, so `fab.py` doesn't have to move them
- SWD test pads (SWDIO, SWCLK, GND) and a reset button, for debugging and recovery without the USB bootloader
- A boot button reachable without pulling a keycap, or a QMK key combo to enter the bootloader
- Wider 5 V lines through each row, so the LED brightness cap isn't the only thing protecting the traces
- A soft-start or load switch on the LED power, to keep VBUS capacitance under USB's 10 µF
- Real 27 Ω USB series resistors instead of the 0 Ω placeholders, in case a daughterboard without its own resistors gets used
