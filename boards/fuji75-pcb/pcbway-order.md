# PCBWay order

Every field on PCBWay's PCB + assembly quote form, top to bottom. The Notes column says when a field is left at the form's default, or what the default was when it's changed.

Upload from `build/fab/` (run `scripts/fab.py` first):

- `fuji75-gerbers.zip`: PCB files
- `fuji75-bom.csv`: BOM
- `fuji75-cpl.csv`: placement (centroid) file

## Assembly Service

| Field | Set to | Notes |
| --- | --- | --- |
| Options | Turnkey | Default. PCBWay sources every part |
| Board type | Single pieces | Default |
| Assembly side(s) | Both sides | Default is Top side. 17 parts on top (controller passives, crystal, boot button), 342 on the bottom |
| Quantity | 2 | Empty by default |
| Contains sensitive components/parts | No | Default |
| Accept alternatives/substitutes made in China | Yes | Default is No. Only for the parts listed in the assembly notes below |
| Function test | No | Default. It needs firmware and a USB daughterboard |
| Firmware loading | No | Default. Flash it yourself over USB with the boot button |
| Select PCBWay's PCB Order# | No | No default selected. The PCB is in the same order |
| Add PO No. | Skip | Default |

### Other Parameters

All empty by default. Filling them in gets an exact price instead of waiting for the quote.

| Field | Set to |
| --- | --- |
| Number of Unique Parts | 18 |
| Number of SMD Parts | 359 |
| Number of BGA/QFP Parts | 2 (RP2040 QFN-56, W25Q16JV USON-8) |
| Number of Through-Hole Parts | 0 |

### Customized Services and Advanced Options

| Field | Set to | Notes |
| --- | --- | --- |
| Depanel the boards to delivery | No | Default. The boards are single pieces |
| Conformal coating | No | Default |
| Press-fit assembly | No | Default |
| Box build assembly | No | Default |
| Cable wire harness assembly | No | Default |
| Package box | Neutral box | Default |
| Flying Probe Testing | No | Default |
| Number of X-ray test | Blank | Default |
| Detailed information of assembly | Paste the text below | Empty by default |

Detailed information of assembly:

```
Both sides are assembled. Placement file covers both sides.
Stabilizers are not included and not in the BOM.
LED1-LED82 (SK6812MINI-E) are reverse-mount: placed on the bottom with the lens facing up through the board cutout.
Substitutes are OK for capacitors, resistors, and D1-D82 (1N4148W). The hotswap socket CPG151101S11 can be replaced with HanElectricity CPG151101S11-2.
No substitutes for U1-U5, Y1, Q1, J1, SW100, or LED1-LED82 without asking first.
Please send part rotation photos for approval before production.
```

## PCB Specifications

| Field | Set to | Notes |
| --- | --- | --- |
| Board type | Single pieces | Default |
| Different design in panel | 1 | Default |
| Size (single) | 310.2 x 121.0 mm | Empty by default. Board outline, PCBWay also reads it from the Gerbers |
| Quantity (single) | 5 | Empty by default. 5 is the minimum, 2 of them get assembled |
| Layers | 2 Layers | Default |
| Material | FR-4 | Default |
| FR4-TG | TG 150-160 | Default |
| Thickness | 1.6 | Default. Same as stock, the plate and case expect it |
| Min track/spacing | 6/6mil | Default. Smallest track and gap are both 0.2 mm (about 7.9 mil) |
| Min hole size | 0.3mm | Default. Vias are 0.3 mm |
| Solder mask | White | Default is Green |
| Silkscreen | Black | Default is White |
| UV printing Multi-color | None | Default |
| Edge connector | No | Default |
| Surface finish | Immersion gold (ENIG) | Default is HASL lead free. ENIG gives flat pads for the QFN and the fine-pitch parts |
| Tick: change HASL to ENIG at PCBWay's discretion | Unticked | Default. Doesn't apply once ENIG is picked |
| Thickness of Immersion Gold | 1U" | Default |
| Via process | Tenting vias | Default. Gerbers decide this anyway |
| Finished copper | 1 oz Cu | Default |
| Remove product No. | Yes (extra $1.5) | Default is No. Otherwise PCBWay prints an order number somewhere on the board |

### Customized Services and Advanced Options

| Field | Set to | Notes |
| --- | --- | --- |
| Peelable soldermask | None | Default |
| Hole copper thickness | Standard (20um) | Default |
| UL marking | None | Default |
| Date code | None | Default |
| Package box | With PCBWay logo | Default |
| Add serial numbers | None | Default |
| Half-cut/Castellated holes | Unticked | Default |
| Edge plating | Unticked | Default |
| Impedance control | Unticked | Default. USB full speed doesn't need it |
| Halogen-free | Unticked | Default |
| Custom stackup | Unticked | Default |
| Carbon ink | Unticked | Default |
| All vias filled with resin and capped | Unticked | Default |
| Via in pad | Unticked | Default |
| Press-fit holes | Unticked | Default |
| Countersink/Counterbore | Unticked | Default |
| Z-axis milling | Unticked | Default |
| Black FR4 (black core) | Unticked | Default |
| Embedded copper PCB | Unticked | Default |
| Cavity PCB | Unticked | Default |
| Semi-Flex PCB | Unticked | Default. The flex cuts are plain milled slots, not this |
| Whole/Partially hybrid PCB | Unticked | Default |
| Back drill PCB | Unticked | Default |
| Leadless partially plated hard gold | Unticked | Default |
| Paper between PCBs | Unticked | Default. Optional, keeps the white boards from scuffing in shipping |
| Other special request | Paste the text below | Empty by default |
| Add PO No. | Skip | Default |

Other special request:

```
Internal cutouts are in the Edge.Cuts layer: 1.0 mm flex cut slots between key rows and rectangular windows for reverse-mount LEDs. Please mill all of them.
```

## Rotation photos

PCBWay sends photos of the part rotations before building. Things to check:

- RP2040, flash, and the SOT-23 parts: the pin 1 dot matches the silkscreen dot
- Diodes: the stripe (cathode) faces the row line (down on most keys, right on the five keys at the right edge)
- LEDs: they're reverse-mount, the lens faces up through the board. Rows 0, 2, and 4 are turned 180 degrees from rows 1, 3, and 5
- Hotswap sockets: the socket's body matches the footprint outline on the bottom
