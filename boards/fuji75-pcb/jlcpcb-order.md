# JLCPCB order

Every field on JLCPCB's PCB + assembly quote form, top to bottom. The Notes column says when a field is left at the form's default, or what the default was when it's changed.

Upload from `build/fab/` (run `scripts/fab.py` first):

- `fuji75-gerbers.zip`: on the quote page, before filling in the form (it sets the size and layers, which can't be edited after)
- `fuji75-bom-jlcpcb.csv`: BOM, after "Next" with assembly turned on
- `fuji75-cpl-jlcpcb.csv`: placement (centroid) file, same step as the BOM. Not `fuji75-cpl.csv`: this one has JLCPCB's rotation offsets (`JLCPCB_ROTATION` in `fab.py`)
- `fuji75-plate-gerbers.zip`: switch plate, a second PCB order in the same cart (see [Switch plate](#switch-plate))

## PCB

| Field | Set to | Notes |
| --- | --- | --- |
| Base Material | FR-4 | Default |
| Layers | 2 | Default. Read from the Gerbers |
| Dimensions | 310.14 x 130.93 mm | Default is 100 x 100. Read from the Gerbers and locked. The board is 310.14 x 120.93, and the edge rails from the assembly section add 10 mm |
| PCB Qty | 5 | Default. 5 is the minimum, 2 of them get assembled |
| Product Type | Industrial/Consumer electronics | Default |

### PCB Specifications

| Field | Set to | Notes |
| --- | --- | --- |
| Different Design | 1 | Default |
| Delivery Format | Single PCB | Default |
| PCB Thickness | 1.6mm | Default. Same as stock, the plate and case expect it |
| PCB Color | White | Default is Green |
| Silkscreen | Black | Default is White. Switches to black on its own with a white board |
| Material Type | FR4 TG135 | Default |
| Surface Finish | ENIG | Default is OSP. ENIG gives flat pads for the QFN and the fine-pitch parts |
| Gold Thickness | 1 U" | Default. Shows up once ENIG is picked. 2 U" is for contacts that get plugged in and out |

### High-spec Options

| Field | Set to | Notes |
| --- | --- | --- |
| Outer Copper Weight | 1 oz | Default |
| Via Covering | Tented | Default |
| Via Plating Method | Not Specified | Default |
| Min via hole size/diameter | 0.3mm/(0.4/0.45mm) | Default. Vias are 0.3 mm with 0.6 mm pads |
| Board Outline Tolerance | ±0.2mm (Regular) | Default |
| Confirm Production file | Yes | Default is No. JLCPCB sends the processed files for approval before making the boards |
| Mark on PCB | Remove Mark | Default. Otherwise JLCPCB prints an order number somewhere on the board |
| Electrical Test | Flying Probe Fully Test | Default |
| Gold Fingers | No | Default |
| Castellated Holes | No | Default |
| Edge Plating | No | Default |
| Blind Slots | No | Default. The flex cuts are full-depth slots |
| UL Marking | No | Default |
| Humidity Indicator Card | No | Default |

### Advanced Options (PCB)

Collapsed by default.

| Field | Set to | Notes |
| --- | --- | --- |
| 4-Wire Kelvin Test | No | Default |
| Paper between PCBs | No | Default |
| Appearance Quality | IPC Class 2 Standard | Default |
| Silkscreen Technology | Ink-jet Printing Silkscreen | Default. Some stock footprint outlines are 0.12 mm and may print faint, which is cosmetic |
| Package Box | With JLCPCB logo | Default |
| Inspection Report | No | Default |
| PCB Remark | Paste the text below | Empty by default |

PCB Remark:

```
Internal cutouts are in the Edge.Cuts layer: 1.0 mm flex cut slots between key rows and rectangular windows for reverse-mount LEDs. Please mill all of them.
```

## PCB Assembly

Turn on the PCB Assembly switch.

| Field | Set to | Notes |
| --- | --- | --- |
| PCBA Type | Standard | Default. Economic can't do both sides |
| Assembly Side | Both Sides | Default is Top Side. 17 parts on top (controller passives, crystal, boot button), 342 on the bottom |
| PCBA Qty | 2 (Custom Qty) | Default is 5 |
| Edge Rails/Fiducials | Added by JLCPCB | Default. The sockets reach the board edge and the board has no fiducials. The rails make it 310.14 x 130.93 mm during assembly |
| Confirm Parts Placement | Yes | Default is No. Check the placement preview before production (see below) |
| Stencil Storage | No | Default |
| Fixture Storage | No | Default |
| Parts Selection | By Customer (Self-Service) | Default. Every BOM line has an LCSC number |

### Advanced Options

| Field | Set to | Notes |
| --- | --- | --- |
| Bake Components | Yes, paste the text below | Default is No. The LEDs are moisture sensitive (MSL 5a). Picking Yes opens a remark box |
| Photo Confirmation | No | Default. Confirm Parts Placement covers it |
| Board Cleaning | No | Default |
| Conformal Coating | No | Default |
| Packaging | Antistatic bubble film | Default |
| Special stencil | No | Default |
| Depanel boards & edge rail before delivery | Yes | Default is No. Breaking the rails off by hand can crack the board at the LED notches on the bottom edge |
| Solder Paste | High temp. | Default (lead-free) |
| Flying Probe Test | No | Default |
| Nitrogen reflow soldering | No | Default |
| Function test | No | Default. It needs firmware and a USB daughterboard |
| Assembly remark | Yes, paste the text below | Default is No |

Bake Components remark:

```
Please bake LED1-LED82 (SK6812MINI-E, LCSC C5149201) before reflow. They are moisture sensitive (MSL 5a). Follow the datasheet or J-STD-033 for bake time and temperature.
```

Assembly remark (the box cuts off at 500 characters, this is 470):

```
Both sides assembled. Stabilizers are not in the BOM.
LED1-LED82 (SK6812MINI-E) are reverse-mount on the bottom, lens facing up through the cutout. Pin 1 (GND) is the pad at the silkscreen triangle. CPL rotations include a 180 degree offset for JLCPCB's library.
SW1-SW82: coordinates are the socket body center.
U2 (USBLC6-2SC6): pin 1 at the silkscreen triangle (the preview shows the dot on pin 6). Pin 2 is GND, pin 5 is 5 V. Turned 180 degrees it shorts 5 V to GND.
```

## BOM and placement

After uploading the BOM and CPL, JLCPCB matches every line by its LCSC number. Check:

- All 18 lines are matched and in stock (if a part is out of stock, stop and look for a replacement before ordering)
- 359 parts placed, 17 on the top and 342 on the bottom
- Extended parts add a setup fee of about $3 each. Most of these parts are extended
- The LED line comes in unselected with a "processing is difficult" warning (reverse mount). Tick it by hand. JLCPCB reviews it after the order and emails if it needs an extra fee
- JLCPCB has been out of the Kailh socket (C2803348). Swap it for the HanElectricity CPG151101S11-2 (C49352235) with the magnifier on that line. It's the same size and fits the same footprint

## Placement preview

The preview shows each part on the board, with JLCPCB's pin 1 as a magenta dot (or a "GND" label on the LEDs) and the board's pin 1 as a black silkscreen triangle. JLCPCB's part library doesn't always match KiCad's rotations. The offsets are in `JLCPCB_ROTATION` in `fab.py` (RP2040 180, regulator 90, flash 90, LEDs 180). Check every part type:

- U1, U3, U4, U5, Q1, J1: the magenta dot sits at the silkscreen triangle, and the part's leads line up with the pads (U4's body lies the long way between its two pad columns)
- U2: the dot shows on the pin 6 corner (a preview quirk, covered in the assembly remark). The body and pin columns should line up with the pads
- Diodes: the stripe (cathode) faces the row line (down on most keys, right on the five keys at the right edge)
- LEDs: "GND" sits on the pad next to the silkscreen triangle. Rows 0, 2, and 4 are turned 180 degrees from rows 1, 3, and 5
- Hotswap sockets: the two pins sit in the plated holes and both metal tabs sit on their pads
- Top side: Y1's pin 1 at its silkscreen dot, and SW100 lined up with its 4 pads the same way as the footprint

## Switch plate

The FR4 switch plate is a separate PCB order (no assembly) added to the same cart. Upload `fuji75-plate-gerbers.zip` on a new quote page. It's a plain white plate with no copper, ordered as the cheapest board that fits: 1 layer, cheapest finish. Fill in the PCB section like this:

| Field | Set to | Notes |
| --- | --- | --- |
| Layers | 1 | Read from the Gerbers (top copper and mask only) |
| Dimensions | 313.38 x 128.48 mm | Read from the Gerbers. Outline including the gasket tabs |
| PCB Qty | 5 | Default. 5 is the minimum |
| PCB Thickness | 1.6mm | Default. Switches clip best into 1.5 mm, but 1.6 mm is the usual FR4 plate thickness and clips fine |
| PCB Color | White | Default is Green |
| Surface Finish | Whichever is cheapest | There's no copper to finish |
| Confirm Production file | Yes | Default is No. Check that every cutout and slot is there before production |
| Mark on PCB | Remove Mark | Default. The plate's top shows between the keycaps |
| PCB Remark | Paste the text below | Empty by default |
| PCB Assembly | Off | Default |

PCB Remark (the box takes 200 characters, this is 134):

```
Keyboard switch plate, no copper. Please mill every Edge.Cuts cutout: switch, stabilizer, 2 mm slots, and 1 mm flex cuts between rows.
```

The underside may come without solder mask (bare FR4) on a 1-layer board. It faces the PCB and doesn't show.

`plate.py --rings` adds a gold ring around each key cutout on the top. That needs ENIG, which costs a lot more on a board this size.
