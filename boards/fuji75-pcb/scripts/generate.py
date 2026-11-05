"""Generates the Fuji75 key grid: schematic sheets, footprints, board outline, and flex cuts.

Run from the repo root with KiCad's bundled Python (kbplacer installed there):

    "C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/generate.py

Pass --no-flex-cuts for a solid board. This rebuilds fuji75.kicad_pcb and the schematic from
scratch, so it refuses to run once the PCB has parts it didn't make (step 2 and later).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

BOARD_DIR = Path(__file__).resolve().parent.parent
PCB_FILE = BOARD_DIR / "fuji75.kicad_pcb"
LIBRARY = "lib/fuji75.pretty"
GENERATED_FILES = [
    "fuji75.kicad_pro",
    "fuji75.kicad_pcb",
    "fuji75.kicad_sch",
    "fuji75-key-matrix.kicad_sch",
    "fuji75-led-chain.kicad_sch",
]

UNIT = 19.05
# Distance from switch centers to the left and right edges (measured), and to the arrow tab.
LEFT_EDGE = 7.73
RIGHT_EDGE = 7.53
ARROW_TAB_BOTTOM = 7.03
ARROW_TAB_RIGHT = 7.73
ARROW_TAB_WIDTH = 52.34
# Every edge moves in by this much for case clearance.
CLEARANCE = 0.2
EDGE_WIDTH = 0.05

FLEX_CUT_WIDTH = 1.0
# Uncut strip at each end of a cut, from the board edge.
FLEX_CUT_END_MARGIN = 10.0
BRIDGE_WIDTH = 4.0
# Each cut: its center in KLE y units, where it starts in mm from the board's left edge, and its
# bridges in mm from the left edge, as a center or a (center, width) pair. Bridges sit where the
# column traces cross. No F-row cut: that strip carries the controller and its traces.
FLEX_CUTS = [
    (2.5, FLEX_CUT_END_MARGIN, [41.93, 79.43, 112, 187]),
    (3.5, FLEX_CUT_END_MARGIN, [47.93, 75, 99.43, 150, 225]),
    # The wide bridge joins the left Shift stabilizer's hole gap.
    (4.5, FLEX_CUT_END_MARGIN, [(36, 12), 69.43, 89.43, 112, 187]),
]
# Space kept between the end of a flex cut and any stabilizer hole edge. It clears the whole
# stabilizer housing, so the housing never straddles a hinge.
HOLE_MARGIN = 4.0
# Socket pads on the outer columns get cut back to this far inside the edge. The socket's metal
# tab hangs past the edge, same as the stock board.
SOCKET_PAD_EDGE_MARGIN = 0.3
# Narrowest board material allowed between two cuts or a cut and the edge (fabs want about 0.5).
MIN_WEB = 1.0

# References this script makes (stabilizers are checked separately).
KEY_COUNT = 82
KEY_REFERENCES = {f"{prefix}{number}" for prefix in ("SW", "D", "LED", "C") for number in range(1, KEY_COUNT + 1)}


def check_board_untouched():
    if not PCB_FILE.exists():
        return
    text = PCB_FILE.read_text(encoding="utf-8")
    references = re.findall(r'\(property "Reference" "([^"]+)"', text)
    # Stabilizers are numbered after their switch, so any number is fine.
    unexpected = [
        reference for reference in references
        if reference not in KEY_REFERENCES and not re.fullmatch(r"ST\d+", reference)
    ]
    if unexpected:
        sys.exit(f"fuji75.kicad_pcb has parts this script didn't make ({', '.join(unexpected[:5])}). Not overwriting it.")
    if re.search(r"\((?:segment|arc|via|zone) ", text):
        sys.exit("fuji75.kicad_pcb has tracks or zones this script didn't make. Not overwriting it.")


def run_kbplacer():
    # kbplacer refuses to overwrite its own output.
    for name in GENERATED_FILES:
        (BOARD_DIR / name).unlink(missing_ok=True)
    subprocess.run(
        [
            sys.executable, "-m", "kbplacer",
            "--layout", "layout.json",
            "--pcb-file", PCB_FILE.name,
            "--create-pcb-file", "--create-led-pcb-elements",
            "--create-sch-file", "--create-led-sch-file", "--bundle-strategy", "hierarchical",
            "--switch-footprint", f"{LIBRARY}:SW_MX_HS_CPG151101S11_{{:g}}u",
            "--stabilizer-footprint", f"{LIBRARY}:STAB_MX_{{:g}}u",
            "--diode-footprint", f"{LIBRARY}:D_SOD-123",
            "--led-footprint", f"{LIBRARY}:LED_MX_6028R",
            "--led-capacitor-footprint", f"{LIBRARY}:C_0402_1005Metric",
            # marbastlib draws these footprints as seen from below. On the back at 180 degrees,
            # the switch pins and socket end up north (south-facing switch).
            "--switch", "SW{} 180 BACK",
            # Offsets are in the switch's rotated frame, so negative y is south on the board.
            "--diode", "D{} CUSTOM -5.5 -4 90 BACK",
            "--additional-elements", "ST{} CUSTOM 0 0 180 FRONT;LED{} CUSTOM 0 -5.08 0 BACK;C{} CUSTOM 5.4 -3 0 BACK",
            "--log-level", "ERROR",
        ],
        cwd=BOARD_DIR,
        check=True,
    )


def key_row(footprints, number):
    """Matrix row (0 to 5) of key number n, read from its diode's cathode net (ROW0 to ROW5)."""
    return int(footprints[f"D{number}"].FindPadByNumber("1").GetNetname().removeprefix("ROW"))


def invert_bottom_row_stabilizers(footprints):
    # In the standard orientation the spacebar stabilizer's large holes run past the bottom edge.
    # The stock board has it upside down too.
    for reference, footprint in footprints.items():
        if reference.startswith("ST") and key_row(footprints, reference[2:]) == 5:
            footprint.Rotate(footprint.GetPosition(), pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))


def snake_led_order(footprints):
    """Switch footprints in LED chain order: row 0 left to right, row 1 right to left, and so on."""
    rows = {}
    for reference, footprint in footprints.items():
        if reference.startswith("SW"):
            rows.setdefault(key_row(footprints, reference[2:]), []).append(footprint)
    order = []
    for row in sorted(rows):
        switches = sorted(rows[row], key=lambda footprint: footprint.GetPosition().x)
        order += switches if row % 2 == 0 else switches[::-1]
    return order


def move_leds_to_snake_order(footprints):
    # kbplacer chains LEDs in matrix order (LED n sits on SW n). The chain in the schematic is
    # just LED1 to LED82, so moving LED n and C n to the nth key in snake order is enough.
    for index, target in enumerate(snake_led_order(footprints), start=1):
        source = footprints[f"SW{index}"].GetPosition()
        for reference in (f"LED{index}", f"C{index}"):
            footprint = footprints[reference]
            footprint.SetPosition(target.GetPosition() + footprint.GetPosition() - source)


def hide_small_part_references(footprints):
    for reference, footprint in footprints.items():
        if not reference.startswith("SW"):
            footprint.Reference().SetVisible(False)


class Grid:
    """Converts KLE units (from the layout's top-left corner) plus a mm offset to board points."""

    def __init__(self, escape_center):
        # Esc's center is at (0.5, 0.75) units in the layout.
        self.origin_x = pcbnew.ToMM(escape_center.x) - 0.5 * UNIT
        self.origin_y = pcbnew.ToMM(escape_center.y) - 0.75 * UNIT

    def x(self, units, offset=0.0):
        return self.origin_x + units * UNIT + offset

    def y(self, units, offset=0.0):
        return self.origin_y + units * UNIT + offset


def point(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def add_edge_shape(board, shape_type, start, end):
    shape = pcbnew.PCB_SHAPE(board, shape_type)
    shape.SetLayer(pcbnew.Edge_Cuts)
    shape.SetWidth(pcbnew.FromMM(EDGE_WIDTH))
    shape.SetStart(point(*start))
    shape.SetEnd(point(*end))
    board.Add(shape)


class Outline:
    """Board edges in mm, already moved in by CLEARANCE."""

    def __init__(self, grid):
        self.left = grid.x(0.5, -LEFT_EDGE + CLEARANCE)
        self.top = grid.y(0.25, CLEARANCE)
        # F-row notch: right of F13 (center x 14.5) and above Insert (center y 2.0).
        self.notch_x = grid.x(15, -CLEARANCE)
        self.notch_y = grid.y(1.5, CLEARANCE)
        self.right = grid.x(16, RIGHT_EDGE - CLEARANCE)
        # Step below PgDn (center y 5.0), where the right edge moves in to the arrow tab.
        self.step_y = grid.y(5.5, -CLEARANCE)
        self.tab_right = grid.x(15.75, ARROW_TAB_RIGHT - CLEARANCE)
        self.tab_bottom = grid.y(6.25, ARROW_TAB_BOTTOM - CLEARANCE)
        self.tab_left = grid.x(15.75, ARROW_TAB_RIGHT - ARROW_TAB_WIDTH + CLEARANCE)
        self.bottom = grid.y(6.5, -CLEARANCE)
        # LED cutouts opened into the bottom edge, as (left x, right x, top y).
        self.led_notches = []

    def points(self):
        return [
            (self.left, self.top), (self.notch_x, self.top), (self.notch_x, self.notch_y),
            (self.right, self.notch_y), (self.right, self.step_y), (self.tab_right, self.step_y),
            (self.tab_right, self.tab_bottom),
            *self.notch_points(self.tab_bottom, self.tab_left, self.tab_right),
            (self.tab_left, self.tab_bottom), (self.tab_left, self.bottom),
            *self.notch_points(self.bottom, self.left, self.tab_left),
            (self.left, self.bottom),
        ]

    def notch_points(self, edge_y, start_x, end_x):
        """Points for the LED notches on one bottom edge, right to left (the outline's direction)."""
        points = []
        for left, right, top in sorted(self.led_notches, reverse=True):
            if start_x < left and right < end_x:
                points += [(right, edge_y), (right, top), (left, top), (left, edge_y)]
        return points

    def right_at(self, y):
        if y < self.notch_y:
            return self.notch_x
        return self.right if y < self.step_y else self.tab_right

    def bottom_at(self, x):
        return self.tab_bottom if x > self.tab_left else self.bottom


def open_edge_led_cutouts(footprints, outline):
    # An LED cutout that ends too close to the bottom edge would leave a strip too thin to make
    # (0.09 mm under the arrow keys). Those cutouts become notches in the edge instead.
    for reference, footprint in footprints.items():
        if not reference.startswith("LED"):
            continue
        cutout = [item for item in footprint.GraphicalItems() if item.GetLayer() == pcbnew.Edge_Cuts]
        # Bounding boxes include the line width, so take half of it back off each side.
        stroke = pcbnew.ToMM(cutout[0].GetWidth()) / 2
        boxes = [item.GetBoundingBox() for item in cutout]
        left = pcbnew.ToMM(min(box.GetX() for box in boxes)) + stroke
        right = pcbnew.ToMM(max(box.GetRight() for box in boxes)) - stroke
        top = pcbnew.ToMM(min(box.GetY() for box in boxes)) + stroke
        bottom = pcbnew.ToMM(max(box.GetBottom() for box in boxes)) - stroke
        if outline.bottom_at((left + right) / 2) - bottom < MIN_WEB:
            # Moving the cutout to a comment layer keeps it visible without cutting the board.
            for item in cutout:
                item.SetLayer(pcbnew.Cmts_User)
            outline.led_notches.append((left, right, top))


def draw_outline(board, outline):
    points = outline.points()
    for start, end in zip(points, points[1:] + points[:1]):
        add_edge_shape(board, pcbnew.SHAPE_T_SEGMENT, start, end)


def trim_socket_pads(footprints, outline):
    left = outline.left + SOCKET_PAD_EDGE_MARGIN
    for reference, footprint in footprints.items():
        if not reference.startswith("SW"):
            continue
        for pad in footprint.Pads():
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            box = pad.GetBoundingBox()
            right = outline.right_at(pcbnew.ToMM(pad.GetPosition().y)) - SOCKET_PAD_EDGE_MARGIN
            left_trim = max(left - pcbnew.ToMM(box.GetX()), 0)
            right_trim = max(pcbnew.ToMM(box.GetRight()) - right, 0)
            if left_trim > 0 or right_trim > 0:
                size = pad.GetSize()
                pad.SetSize(pcbnew.VECTOR2I(size.x - pcbnew.FromMM(left_trim + right_trim), size.y))
                pad.SetPosition(pad.GetPosition() + point((left_trim - right_trim) / 2, 0))


def stabilizer_holes(footprints):
    """(x, y, radius) in mm for every stabilizer hole."""
    holes = []
    for reference, footprint in footprints.items():
        if reference.startswith("ST"):
            for pad in footprint.Pads():
                position = pad.GetPosition()
                holes.append((pcbnew.ToMM(position.x), pcbnew.ToMM(position.y), pcbnew.ToMM(pad.GetSizeX()) / 2))
    return holes


def subtract(spans, gap_start, gap_end):
    result = []
    for start, end in spans:
        if gap_end <= start or gap_start >= end:
            result.append((start, end))
            continue
        if gap_start > start:
            result.append((start, gap_start))
        if gap_end < end:
            result.append((gap_end, end))
    return result


def draw_flex_cuts(board, grid, outline, holes):
    for center_row, start, bridges in FLEX_CUTS:
        center_y = grid.y(center_row)
        spans = [(outline.left + start, outline.right_at(center_y) - FLEX_CUT_END_MARGIN)]
        for bridge in bridges:
            center, width = bridge if isinstance(bridge, tuple) else (bridge, BRIDGE_WIDTH)
            center_x = outline.left + center
            spans = subtract(spans, center_x - width / 2, center_x + width / 2)
        for hole_x, hole_y, radius in holes:
            if abs(hole_y - center_y) < radius + FLEX_CUT_WIDTH / 2 + HOLE_MARGIN:
                spans = subtract(spans, hole_x - radius - HOLE_MARGIN, hole_x + radius + HOLE_MARGIN)
        for start, end in spans:
            add_edge_shape(
                board,
                pcbnew.SHAPE_T_RECTANGLE,
                (start, center_y - FLEX_CUT_WIDTH / 2),
                (end, center_y + FLEX_CUT_WIDTH / 2),
            )


def check_holes_inside(board):
    # DRC doesn't flag a hole that crosses the board edge, so check every hole's extremes.
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    broken = set()
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            radius = pad.GetDrillSizeX() // 2
            if radius == 0:
                continue
            center = pad.GetPosition()
            for offset_x, offset_y in ((radius, 0), (-radius, 0), (0, radius), (0, -radius)):
                if not outline.Contains(center + pcbnew.VECTOR2I(offset_x, offset_y)):
                    broken.add(footprint.GetReference())
    if broken:
        sys.exit(f"Holes cross the board edge or a flex cut: {', '.join(sorted(broken))}")


def check_min_web(board):
    # Shrinking the board shape by half the minimum web merges any cutout that sits closer than
    # that to the edge or another cutout, so the hole count drops.
    shape = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(shape, False)
    holes = shape.HoleCount(0)
    shape.Deflate(pcbnew.FromMM(MIN_WEB / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.01))
    if shape.OutlineCount() != 1 or shape.HoleCount(0) != holes:
        sys.exit(f"Some board material between cuts or edges is thinner than {MIN_WEB} mm.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-flex-cuts", action="store_true", help="draw the outline without flex cuts")
    args = parser.parse_args()

    check_board_untouched()
    run_kbplacer()

    board = pcbnew.LoadBoard(str(PCB_FILE))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    invert_bottom_row_stabilizers(footprints)
    move_leds_to_snake_order(footprints)
    hide_small_part_references(footprints)

    grid = Grid(footprints["SW1"].GetPosition())
    outline = Outline(grid)
    open_edge_led_cutouts(footprints, outline)
    draw_outline(board, outline)
    trim_socket_pads(footprints, outline)
    if not args.no_flex_cuts:
        draw_flex_cuts(board, grid, outline, stabilizer_holes(footprints))
    check_holes_inside(board)
    check_min_web(board)

    board.Save(str(PCB_FILE))
    print(f"Wrote {PCB_FILE}")


if __name__ == "__main__":
    main()
