# pcbs

This is where I keep my PCB designs.

Each board lives in `boards/<board>/`. Boards are designed in KiCad 10 and made by PCBWay.

## Printing at actual size

Paper prints of board outlines (for fit checks against a real board) have to come out 1:1. Measure a known line on the print before trusting it.

The Brother HL-L2305 needs Brother's own driver for this. With Windows' generic Microsoft IPP Class Driver it shrinks every page to about 95%, even with "Actual size" selected and the driver's scaling set to None.

## License

Hardware (KiCad files, fab files, and everything else outside `firmware/` folders) is under the CERN Open Hardware Licence v2, Permissive (CERN-OHL-P-2.0, see `LICENSE`). Firmware in `boards/<board>/firmware/` is under GPL-2.0-or-later (see the `LICENSE` in that folder), the same as QMK.
