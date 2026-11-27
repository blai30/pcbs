"""Writes the PCBWay and JLCPCB order files to build/fab/: zipped Gerbers and drill files, the BOM,
the placement (CPL) file for both sides, the plate Gerbers, and a STEP model of the plate for CNC.

Run from the repo root with KiCad's bundled Python:

    "C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/fab.py
"""

import csv
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pcbnew

KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
BOARD_DIR = Path(__file__).resolve().parent.parent
PCB = BOARD_DIR / "fuji75.kicad_pcb"
SCHEMATIC = BOARD_DIR / "fuji75.kicad_sch"
# Built by plate.py.
PLATE = BOARD_DIR / "plate" / "fuji75-plate.kicad_pcb"
OUT = BOARD_DIR / "build" / "fab"
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
# The plate is ordered as a 1-layer board with no holes.
PLATE_LAYERS = "F.Cu,F.Mask,Edge.Cuts"
# CNC plates (PC, POM) are as thick as the stock aluminum plate.
CNC_PLATE_THICKNESS = 1.5

# Degrees added to KiCad's rotation for JLCPCB, by LCSC part number. Their part library holds
# these parts turned from KiCad's convention (checked against pin 1 in their placement preview).
JLCPCB_ROTATION = {
    # RP2040
    "C2040": 180,
    # AP2112K-3.3
    "C51118": 90,
    # W25Q16JV
    "C2843335": 90,
    # SK6812MINI-E
    "C5149201": 180,
}


def cli(*args):
    subprocess.run([KICAD_CLI, *args], check=True, capture_output=True)


def gerbers(board, name, layers=LAYERS, holes=True):
    folder = OUT / name
    folder.mkdir(parents=True)
    cli("pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask", "-o", f"{folder}/", str(board))
    if holes:
        cli("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
            "--map-format", "gerberx2", "-o", f"{folder}/", str(board))
    else:
        # The job file's stackup (2 layers, ENIG) comes from the PCB. Leave it out so the fab
        # reads the plate's layers from the Gerbers.
        next(folder.glob("*.gbrjob")).unlink()
    with zipfile.ZipFile(OUT / f"{name}.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.iterdir()):
            archive.write(path, path.name)


def cnc_plate():
    """The plate as a STEP model for CNC machining, at CNC_PLATE_THICKNESS."""
    # KiCad's STEP export takes the thickness from the stackup's core layer. pcbnew's Python API
    # can't reach the stackup, so this edits the file.
    text, count = re.subn(r'(\(type "core"\)\s*\(thickness )[\d.]+', rf"\g<1>{CNC_PLATE_THICKNESS}", PLATE.read_text(encoding="utf-8"))
    if count != 1:
        sys.exit(f"Expected one core layer in {PLATE}, found {count}")
    thinner = OUT / "plate-cnc.kicad_pcb"
    thinner.write_text(text, encoding="utf-8")
    cli("pcb", "export", "step", "--board-only", "-o", str(OUT / f"fuji75-plate-{CNC_PLATE_THICKNESS}mm.step"), str(thinner))
    # kicad-cli leaves a project settings file next to it.
    for path in (thinner, thinner.with_suffix(".kicad_prl")):
        path.unlink(missing_ok=True)


def bom():
    """PCBWay's BOM columns, one line per part number."""
    raw = OUT / "bom-raw.csv"
    cli("sch", "export", "bom", "--fields", "Reference,${QUANTITY},MPN,LCSC,Value,Footprint",
        "--labels", "Designator,Qty,MPN,LCSC,Value,Footprint", "--group-by", "Value,MPN",
        "--exclude-dnp", "-o", str(raw), str(SCHEMATIC))
    designators = {}
    with (raw.open(encoding="utf-8") as source,
          (OUT / "fuji75-bom.csv").open("w", newline="", encoding="utf-8") as pcbway_file,
          (OUT / "fuji75-bom-jlcpcb.csv").open("w", newline="", encoding="utf-8") as jlcpcb_file):
        pcbway = csv.writer(pcbway_file)
        pcbway.writerow(["Item #", "Designator", "Qty", "Mfg Part #", "LCSC Part #", "Description / Value", "Package/Footprint"])
        # JLCPCB wants every designator listed, not ranges.
        jlcpcb = csv.writer(jlcpcb_file)
        jlcpcb.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for item, row in enumerate(csv.DictReader(source), start=1):
            footprint = row["Footprint"].split(":")[-1]
            pcbway.writerow([item, row["Designator"], row["Qty"], row["MPN"], row["LCSC"], row["Value"], footprint])
            references = expand(row["Designator"])
            jlcpcb.writerow([row["MPN"], ",".join(sorted(references, key=natural)), footprint, row["LCSC"]])
            designators.update(dict.fromkeys(references, row["LCSC"]))
    raw.unlink()
    # Designator to LCSC part number.
    return designators


def natural(reference):
    """'C10' sorts after 'C9'."""
    prefix = reference.rstrip("0123456789")
    return prefix, int(reference[len(prefix):])


def expand(field):
    """'C1-C3,C9' to {'C1', 'C2', 'C3', 'C9'}."""
    result = set()
    for part in field.split(","):
        if "-" in part:
            start, end = part.split("-")
            prefix = start.rstrip("0123456789")
            result.update(f"{prefix}{number}" for number in range(int(start[len(prefix):]), int(end[len(prefix):]) + 1))
        else:
            result.add(part)
    return result


def socket_centers():
    """Hotswap socket body centers (midpoint of the two plated pin holes), in the position file's
    frame. The socket footprints have their origin at the switch center, about 3.8 mm away."""
    board = pcbnew.LoadBoard(str(PCB))
    centers = {}
    for footprint in board.GetFootprints():
        if not footprint.GetFPIDAsString().split(":")[-1].startswith("SW_MX_HS"):
            continue
        holes = [pad.GetPosition() for pad in footprint.Pads() if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        x = pcbnew.ToMM(sum(hole.x for hole in holes)) / len(holes)
        y = pcbnew.ToMM(sum(hole.y for hole in holes)) / len(holes)
        # The position file has Y pointing up.
        centers[footprint.GetReference()] = (x, -y)
    return centers


def placement(designators):
    """PCBWay's CPL columns for every part in the BOM (JLCPCB uses the same ones)."""
    raw = OUT / "pos-raw.csv"
    cli("pcb", "export", "pos", "--side", "both", "--format", "csv", "--units", "mm", "--exclude-dnp", "-o", str(raw), str(PCB))
    sockets = socket_centers()
    placed = set()
    with (raw.open(encoding="utf-8") as source,
          (OUT / "fuji75-cpl.csv").open("w", newline="", encoding="utf-8") as pcbway_file,
          (OUT / "fuji75-cpl-jlcpcb.csv").open("w", newline="", encoding="utf-8") as jlcpcb_file):
        pcbway = csv.writer(pcbway_file)
        jlcpcb = csv.writer(jlcpcb_file)
        for writer in (pcbway, jlcpcb):
            writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in csv.DictReader(source):
            reference = row["Ref"]
            if reference not in designators:
                continue
            x, y = sockets.get(reference, (float(row["PosX"]), float(row["PosY"])))
            position = [reference, f"{x:.3f}mm", f"{y:.3f}mm", "Top" if row["Side"] == "top" else "Bottom"]
            rotation = float(row["Rot"])
            pcbway.writerow([*position, f"{rotation:g}"])
            jlcpcb_rotation = rotation + JLCPCB_ROTATION.get(designators[reference], 0)
            jlcpcb.writerow([*position, f"{jlcpcb_rotation % 360:g}"])
            placed.add(reference)
    raw.unlink()
    return placed


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    gerbers(PCB, "fuji75-gerbers")
    gerbers(PLATE, "fuji75-plate-gerbers", PLATE_LAYERS, holes=False)
    cnc_plate()
    designators = bom()
    placed = placement(designators)
    missing = set(designators) - placed
    if missing:
        sys.exit(f"In the BOM but not in the placement file: {', '.join(sorted(missing))}")
    print(f"Wrote {OUT}: {len(designators)} parts placed")


if __name__ == "__main__":
    main()
