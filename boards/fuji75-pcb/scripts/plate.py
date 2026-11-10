"""Builds plate/fuji75-plate.kicad_pcb, an FR4 switch plate for this PCB.

Starts from the stock plate DXF (outline, T-shaped gasket tabs) and swaps its multi-layout
cutouts for ones that fit this PCB's layout, placed from the PCB's switch and stabilizer
footprints. The plate shares the PCB's coordinates.

Flex comes from the stock plate's vertical slots between keys plus long cuts between rows (the
printed plate's pattern). --no-row-cuts leaves the row cuts off (the stiffer stock plate).

The plate has no copper, for the cheapest order (1 layer, any finish). --rings adds a gold ring
around each key cutout on the top: bare copper with the solder mask opened over it, which needs
ENIG.

It also writes plate/fuji75-plate-foam.dxf and .pdf (1:1), the foam that sits between the plate and the PCB.

Run from the repo root with KiCad's bundled Python:

    "C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/plate.py [--no-row-cuts] [--rings]

It needs ezdxf and shapely, installed once with
"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user ezdxf shapely
"""

import sys
from pathlib import Path

import ezdxf
import pcbnew
from ezdxf import path as dxf_path
from shapely import LineString, Point, Polygon, affinity, box, unary_union
from shapely.ops import polygonize_full

BOARD_DIR = Path(__file__).resolve().parent.parent
PCB = BOARD_DIR / "fuji75.kicad_pcb"
DXF = BOARD_DIR / "fuji75_plate.dxf"
PLATE = BOARD_DIR / "plate" / "fuji75-plate.kicad_pcb"
FOAM = BOARD_DIR / "plate" / "fuji75-plate-foam.dxf"
# Blank space around the foam on the PDF page.
PDF_MARGIN = 10.0

SWITCH_CUTOUT = 14.0
CORNER_RADIUS = 0.5
# Stock cutouts narrower than this are flex slots.
SLOT_WIDTH = 3.5
# Narrowest material allowed next to a new cutout. Stock webs are 1.5 mm.
MIN_WEB = 1.0
# Stock cutouts kept as drawn, by the switch they hold: the backspace (the template for the other
# 2u and 2.25u keys) and the wide spacebar cutout that leaves the boot button reachable.
STOCK_CUTOUTS = {"backspace": "SW28", "spacebar": "SW76"}
# 6.25u stabilizer cutouts relative to each stabilizer: the stock plate's height, 7 mm wide like
# the backspace's stabilizer notches.
SPACE_STAB = (-3.5, -10.5, 3.5, 7.0)
CUT_WIDTH = 1.0
# Gold ring around each key cutout, as its inner and outer distance from the cutout edge. JLCPCB
# needs copper 0.3 mm from milled edges (the edge clearance in fuji75-plate.kicad_pro).
RING = (0.35, 1.0)
BRIDGE_WIDTH = 3.0
# Row cuts stop this far from any cutout or slot (stock webs are 1.5 mm). Under Enter and backspace
# that leaves the stabilizer notches in solid plate.
CUT_CLEARANCE = 1.5
# Cuts along the middle of the web between rows, as (y, start x, end x, bridge centers), from the
# printed plate. Bridges are staggered from row to row. The web above the spacebar has none (its
# cutouts break it up already).
ROW_CUTS = [
    (50.01, 33.08, 307.08, [74.08, 139.08, 229.08, 289.08]),
    (71.44, 33.08, 338.08, [104.08, 159.08, 209.08, 319.08]),
    (90.49, 33.08, 338.08, [74.08, 139.08, 229.08, 289.08]),
    (109.54, 33.08, 338.08, [104.08, 159.08, 209.08, 319.08]),
]


def read_dxf():
    """The stock plate's outline and cutouts, in the DXF's coordinates."""
    # Some segment ends miss each other by about 0.01 mm. Snap ends closer than 0.02 mm together.
    ends = []

    def snap(point):
        for end in ends:
            if abs(end[0] - point[0]) < 0.02 and abs(end[1] - point[1]) < 0.02:
                return end
        ends.append(point)
        return point

    lines = []
    for entity in ezdxf.readfile(DXF).modelspace():
        points = [(vertex.x, vertex.y) for vertex in dxf_path.make_path(entity).flattening(0.002)]
        # The DXF has zero-length fragments.
        if len(points) < 2 or LineString(points).length < 1e-4:
            continue
        points[0], points[-1] = snap(points[0]), snap(points[-1])
        lines.append(LineString(points))
    faces, _, dangles, _ = polygonize_full(unary_union(lines))
    if not dangles.is_empty:
        sys.exit(f"DXF has {len(dangles.geoms)} open edges")
    plate = max(faces.geoms, key=lambda face: face.area)
    # Fragments that touch leave zero-area rings behind.
    cutouts = [Polygon(ring) for ring in plate.interiors]
    return Polygon(plate.exterior), [cutout for cutout in cutouts if cutout.area > 0.01]


def is_switch_cutout(shape):
    min_x, min_y, max_x, max_y = shape.bounds
    return abs(max_x - min_x - SWITCH_CUTOUT) < 0.05 and abs(max_y - min_y - SWITCH_CUTOUT) < 0.05


def to_pcb(outline, cutouts, switches):
    """Moves the DXF onto the PCB, checked against every stock switch cutout."""
    # The DXF is drawn upside down, and KiCad's y axis points down, so x flips and y doesn't.
    flip = lambda shape, x, y: affinity.affine_transform(shape, [-1, 0, 0, 1, x, y])
    centers = [cutout.centroid for cutout in cutouts if is_switch_cutout(cutout)]
    # Esc: the top-left switch on both.
    esc_cutout = min(centers, key=lambda center: (round(center.y), -center.x))
    esc = min(switches.values(), key=lambda center: (round(center[1]), center[0]))
    x, y = esc[0] + esc_cutout.x, esc[1] - esc_cutout.y
    for center in centers:
        moved = flip(center, x, y)
        if min(moved.distance(Point(switch)) for switch in switches.values()) > 0.05:
            sys.exit(f"Stock switch cutout at {moved.coords[0]} has no switch on the PCB")
    return flip(outline, x, y), [flip(cutout, x, y) for cutout in cutouts]


def rounded(left, top, right, bottom):
    return box(left, top, right, bottom).buffer(-CORNER_RADIUS).buffer(CORNER_RADIUS, quad_segs=8)


def layout_cutouts(cutouts, switches, stabilizers):
    """Keeps the stock cutouts that fit this layout and adds the rest from the PCB footprints."""
    holding = lambda cutout: [ref for ref, center in switches.items() if cutout.contains(Point(center))]
    stock = {name: next(cutout for cutout in cutouts if STOCK_CUTOUTS[name] in holding(cutout)) for name in STOCK_CUTOUTS}
    kept, slots, dropped = list(stock.values()), [], []
    for cutout in cutouts:
        min_x, _, max_x, _ = cutout.bounds
        if max_x - min_x < SLOT_WIDTH:
            slots.append(cutout)
        elif is_switch_cutout(cutout):
            kept.append(cutout)
        elif not any(cutout is shape for shape in stock.values()):
            dropped.append(cutout)

    backspace = switches[STOCK_CUTOUTS["backspace"]]
    covered = unary_union(kept)
    added = []
    for ref, (x, y) in switches.items():
        if covered.contains(Point(x, y)):
            continue
        size = stabilizers.get(ref)
        if size in ("2u", "2.25u"):
            added.append(affinity.translate(stock["backspace"], x - backspace[0], y - backspace[1]))
        elif size is None:
            half = SWITCH_CUTOUT / 2
            added.append(rounded(x - half, y - half, x + half, y + half))
        else:
            sys.exit(f"No cutout for {ref} with a {size} stabilizer")
    for ref, size in stabilizers.items():
        if size == "6.25u":
            x, y = switches[ref]
            left, top, right, bottom = SPACE_STAB
            added += [rounded(x + side * 50.006 + left, y + top, x + side * 50.006 + right, y + bottom) for side in (-1, 1)]

    print(f"Kept {len(kept)} stock cutouts, replaced {len(dropped)} multi-layout cutouts with {len(added)}")
    return kept + added, added, slots


def stock_slots(keys, added, slots, switches):
    """The stock plate's vertical slots between keys, plus matching ones between new keys."""
    # Stock slots that would leave thin material next to a new cutout go.
    new = unary_union(added)
    kept = [slot for slot in slots if slot.distance(new) >= MIN_WEB]
    # The stock plate has a slot between each pair of switches 1u apart in a row. Copy one in
    # between new switches that don't have one.
    template = next(slot for slot in slots if round(slot.bounds[2] - slot.bounds[0], 1) == 2.0)
    slot_area = unary_union(kept)
    extra = []
    for ref, (x, y) in switches.items():
        if not new.contains(Point(x, y)):
            continue
        for other_x, other_y in switches.values():
            middle = Point((x + other_x) / 2, y)
            if abs(other_y - y) < 0.01 and abs(other_x - x - 19.05) < 0.1 and not slot_area.contains(middle):
                extra.append(affinity.translate(template, middle.x - template.centroid.x, middle.y - template.centroid.y))
    print(f"Kept {len(kept)} of {len(slots)} stock slots, added {len(extra)}")
    return kept + extra


def row_cuts(avoid):
    radius = CUT_WIDTH / 2
    keep_out = unary_union(avoid).buffer(CUT_CLEARANCE + radius)
    cuts = []
    for y, start, end, bridges in ROW_CUTS:
        edges = [start] + [edge for center in bridges for edge in (center - BRIDGE_WIDTH / 2, center + BRIDGE_WIDTH / 2)] + [end]
        for i in range(0, len(edges), 2):
            # Shortened by the round ends' reach.
            line = LineString([(edges[i] + radius, y), (edges[i + 1] - radius, y)]).difference(keep_out)
            # Pieces left over between two keep-outs aren't worth cutting.
            cuts += [piece.buffer(radius, quad_segs=8) for piece in getattr(line, "geoms", [line]) if piece.length > 2]
    print(f"Added {len(cuts)} row cuts")
    return cuts


def thin(shape):
    """Material in the shape narrower than MIN_WEB."""
    half = MIN_WEB / 2 - 0.05
    return shape.difference(shape.buffer(-half, join_style="mitre").buffer(half, join_style="mitre"))


def check(outline, keys, added, holes, stock, switches, button):
    # Stock cutouts sit up to 0.014 mm off the PCB's switch centers.
    area = unary_union(holes).buffer(0.02)
    half = SWITCH_CUTOUT / 2
    for ref, (x, y) in switches.items():
        if not area.contains(rounded(x - half, y - half, x + half, y + half)):
            sys.exit(f"{ref} isn't fully inside a cutout")
    if not area.contains(button):
        sys.exit("The boot button isn't fully inside a cutout")
    if not all(outline.contains(hole) for hole in holes):
        sys.exit("A cutout runs past the outline")
    for cutout in added:
        others = unary_union([other for other in keys if other is not cutout])
        if min(cutout.distance(others), cutout.distance(outline.exterior)) < MIN_WEB:
            sys.exit(f"Cutout at {cutout.centroid.coords[0]} leaves material under {MIN_WEB} mm")
    plate = outline.difference(unary_union(holes))
    if plate.geom_type != "Polygon":
        sys.exit(f"The cuts split the plate into {len(plate.geoms)} pieces")
    # Thin spots the stock plate doesn't already have (it has a few next to its slots).
    spots = thin(plate).difference(thin(outline.difference(unary_union(stock))).buffer(0.05))
    spots = [spot for spot in getattr(spots, "geoms", [spots]) if spot.area > 0.05]
    if spots:
        sys.exit(f"Material under {MIN_WEB} mm at {[tuple(round(value, 1) for value in spot.centroid.coords[0]) for spot in spots]}")


def gold_rings(outline, keys, holes):
    rings = unary_union([key.buffer(RING[1], quad_segs=8).difference(key.buffer(RING[0], quad_segs=8)) for key in keys])
    # Stays the same distance off every edge, flex cuts and the outline included.
    rings = rings.difference(unary_union(holes).buffer(RING[0], quad_segs=8)).intersection(outline.buffer(-RING[0]))
    return list(getattr(rings, "geoms", [rings]))


def add_polygon(board, polygon, layer):
    shape = pcbnew.SHAPE_POLY_SET()
    for index, ring in enumerate([polygon.exterior, *polygon.interiors]):
        chain = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in ring.coords[:-1]:
            chain.Append(pcbnew.VECTOR2I_MM(x, y))
        chain.SetClosed(True)
        if index == 0:
            shape.AddOutline(chain)
        else:
            shape.AddHole(chain, 0)
    # Graphic polygons can't hold holes. Fracturing joins each hole to the outline.
    shape.Fracture()
    graphic = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
    graphic.SetPolyShape(shape)
    graphic.SetFilled(True)
    graphic.SetWidth(0)
    graphic.SetLayer(layer)
    board.Add(graphic)


def write_plate(pcb, outline, cutouts, rings):
    plate = pcbnew.CreateEmptyBoard()
    # Same stackup as the PCB: 1.6 mm FR4, white mask, black silkscreen.
    plate.SetDesignSettings(pcb.GetDesignSettings())
    for shape in [outline, *cutouts]:
        points = shape.simplify(0.002).exterior.coords
        for start, end in zip(points, points[1:]):
            segment = pcbnew.PCB_SHAPE(plate, pcbnew.SHAPE_T_SEGMENT)
            segment.SetStart(pcbnew.VECTOR2I_MM(*start))
            segment.SetEnd(pcbnew.VECTOR2I_MM(*end))
            segment.SetLayer(pcbnew.Edge_Cuts)
            segment.SetWidth(pcbnew.FromMM(0.05))
            plate.Add(segment)
    for ring in rings:
        # Copper plus a matching mask opening.
        for layer in (pcbnew.F_Cu, pcbnew.F_Mask):
            add_polygon(plate, ring.simplify(0.002), layer)
    PLATE.parent.mkdir(exist_ok=True)
    plate.Save(str(PLATE))


# Plate foam: the PCB outline pulled in, with a hole for each switch and whole regions cut out where
# something stands up from the PCB.
FOAM_INSET = 0.5
# Below the plate a switch is 14 mm square. The extra keeps the foam off its clips.
FOAM_SWITCH_HOLE = 15.0
# Stabilizer housings sit over their two PCB holes: the foam clears both holes by this much, across
# FOAM_STAB_WIDTH (the housing is about 6.6 mm wide). The wire runs above the plate.
FOAM_STAB_CLEARANCE = 0.75
FOAM_STAB_WIDTH = 8.0
# Clearance around the parts on top of the PCB (the controller passives, crystal, and boot button).
FOAM_PART_CLEARANCE = 1.5
# Foam narrower than this tears. Holes closer together than this merge into one.
FOAM_MIN_WEB = 1.9


def foam(pcb, switches):
    """The foam sheet as a polygon."""
    outlines = pcbnew.SHAPE_POLY_SET()
    pcb.GetBoardPolygonOutlines(outlines, False)
    chain = outlines.Outline(0)
    outline = Polygon([(pcbnew.ToMM(chain.CPoint(i).x), pcbnew.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())])
    sheet = outline.buffer(-FOAM_INSET, join_style="mitre")

    half = FOAM_SWITCH_HOLE / 2
    holes = [box(x - half, y - half, x + half, y + half) for x, y in switches.values()]
    for footprint in pcb.GetFootprints():
        ref = footprint.GetReference()
        if ref.startswith("ST"):
            pads = [(pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y), pcbnew.ToMM(pad.GetDrillSize().x) / 2) for pad in footprint.Pads()]
            for x in {round(pad_x, 3) for pad_x, _, _ in pads}:
                housing = [(pad_y, radius) for pad_x, pad_y, radius in pads if abs(pad_x - x) < 0.01]
                top = min(pad_y - radius for pad_y, radius in housing) - FOAM_STAB_CLEARANCE
                bottom = max(pad_y + radius for pad_y, radius in housing) + FOAM_STAB_CLEARANCE
                holes.append(box(x - FOAM_STAB_WIDTH / 2, top, x + FOAM_STAB_WIDTH / 2, bottom))
        elif footprint.GetLayer() == pcbnew.F_Cu and not ref.startswith(("SW", "ST")) or ref == "SW100":
            bounds = footprint.GetBoundingBox(False)
            holes.append(box(*(pcbnew.ToMM(value) for value in (bounds.GetLeft(), bounds.GetTop(), bounds.GetRight(), bounds.GetBottom()))).buffer(FOAM_PART_CLEARANCE, join_style="mitre"))
    # Merges holes closer than FOAM_MIN_WEB to each other or to the edge (those open into the edge),
    # which also fills the gaps between the controller parts into one region.
    closing = FOAM_MIN_WEB / 2
    outside = sheet.envelope.buffer(10).difference(sheet)
    cut = unary_union([*holes, outside]).buffer(closing, join_style="mitre").buffer(-closing, join_style="mitre")
    pieces = sheet.difference(cut)
    pieces = sorted(getattr(pieces, "geoms", [pieces]), key=lambda piece: piece.area)
    # Merged regions can leave small islands of foam. They'd just fall out, so they go too.
    for island in pieces[:-1]:
        print(f"Dropped a {island.area:.0f} mm² foam island at {tuple(round(value, 1) for value in island.centroid.coords[0])}")
    return pieces[-1]


def write_foam(shape):
    document = ezdxf.new(units=ezdxf.units.MM)
    space = document.modelspace()
    for ring in [shape.exterior, *shape.interiors]:
        # DXF's y axis points up. Flip so the foam reads the right way up.
        space.add_lwpolyline([(x, -y) for x, y in ring.coords], close=True)
    document.saveas(FOAM)
    write_pdf(shape, FOAM.with_suffix(".pdf"))
    min_x, min_y, max_x, max_y = shape.bounds
    print(f"Wrote {FOAM} and .pdf: {max_x - min_x:.1f} x {max_y - min_y:.1f} mm, {len(shape.interiors)} holes")


def write_pdf(shape, path):
    """A one-page vector PDF at 1:1, on a page the size of the shape plus PDF_MARGIN."""
    points_per_mm = 72 / 25.4
    min_x, min_y, max_x, max_y = shape.bounds
    width, height = (max_x - min_x + 2 * PDF_MARGIN) * points_per_mm, (max_y - min_y + 2 * PDF_MARGIN) * points_per_mm
    # PDF's y axis points up, KiCad's points down.
    to_page = lambda x, y: ((x - min_x + PDF_MARGIN) * points_per_mm, height - (y - min_y + PDF_MARGIN) * points_per_mm)
    paths = []
    for ring in [shape.exterior, *shape.interiors]:
        start, *rest = [to_page(x, y) for x, y in ring.coords]
        paths.append(f"{start[0]:.3f} {start[1]:.3f} m " + " ".join(f"{x:.3f} {y:.3f} l" for x, y in rest) + " h S")
    # Hairline black strokes.
    content = ("0.25 w 0 0 0 RG\n" + "\n".join(paths)).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.3f} {height:.3f}] /Contents 4 0 R >>".encode("ascii"),
        f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"
    table = len(output)
    output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii")
    output += b"".join(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets)
    output += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{table}\n%%EOF\n".encode("ascii")
    path.write_bytes(bytes(output))


def main():
    pcb = pcbnew.LoadBoard(str(PCB))
    center = lambda footprint: (pcbnew.ToMM(footprint.GetPosition().x), pcbnew.ToMM(footprint.GetPosition().y))
    footprints = {footprint.GetReference(): footprint for footprint in pcb.GetFootprints()}
    switches = {ref: center(footprint) for ref, footprint in footprints.items() if footprint.GetFPIDAsString().startswith("fuji75:SW_MX")}
    # Stabilizer size by the switch it sits under (ST28 sits under SW28).
    stabilizers = {"SW" + ref[2:]: footprint.GetFPIDAsString().split("_")[-1] for ref, footprint in footprints.items() if ref.startswith("ST")}
    bounds = footprints["SW100"].GetBoundingBox(False)
    button = box(*(pcbnew.ToMM(value) for value in (bounds.GetLeft(), bounds.GetTop(), bounds.GetRight(), bounds.GetBottom())))

    outline, cutouts = to_pcb(*read_dxf(), switches)
    keys, added, slots = layout_cutouts(cutouts, switches, stabilizers)
    flex = stock_slots(keys, added, slots, switches)
    if "--no-row-cuts" not in sys.argv:
        flex += row_cuts(keys + flex)
    holes = keys + flex
    check(outline, keys, added, holes, cutouts, switches, button)
    rings = gold_rings(outline, keys, holes) if "--rings" in sys.argv else []
    write_plate(pcb, outline, holes, rings)
    print(f"Wrote {PLATE}")
    write_foam(foam(pcb, switches))


if __name__ == "__main__":
    main()
