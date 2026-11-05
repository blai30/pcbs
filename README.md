# pcbs

This is where I keep my PCB designs.

Each board lives in `boards/<board>/`. Boards are designed in KiCad 10 and made by PCBWay.

## Printing at actual size

Paper prints of board outlines (for fit checks against a real board) have to come out 1:1. Measure a known line on the print before trusting it.

The Brother HL-L2305 needs Brother's own driver for this. With Windows' generic Microsoft IPP Class Driver it shrinks every page to about 95%, even with "Actual size" selected and the driver's scaling set to None.
