"""Writes the PCBWay order files to build/fab/: zipped Gerbers and drill files, the BOM, and the
placement (CPL) file for both sides.

Run from the repo root with KiCad's bundled Python:

    "C:/Program Files/KiCad/10.0/bin/python.exe" boards/fuji75-pcb/scripts/fab.py
"""

import csv
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
BOARD_DIR = Path(__file__).resolve().parent.parent
PCB = BOARD_DIR / "fuji75.kicad_pcb"
SCHEMATIC = BOARD_DIR / "fuji75.kicad_sch"
OUT = BOARD_DIR / "build" / "fab"
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def cli(*args):
    subprocess.run([KICAD_CLI, *args], check=True, capture_output=True)


def gerbers():
    folder = OUT / "gerbers"
    folder.mkdir(parents=True)
    cli("pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "-o", f"{folder}/", str(PCB))
    cli("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
        "--map-format", "gerberx2", "-o", f"{folder}/", str(PCB))
    with zipfile.ZipFile(OUT / "fuji75-gerbers.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.iterdir()):
            archive.write(path, path.name)


def bom():
    """PCBWay's BOM columns, one line per part number."""
    raw = OUT / "bom-raw.csv"
    cli("sch", "export", "bom", "--fields", "Reference,${QUANTITY},MPN,LCSC,Value,Footprint",
        "--labels", "Designator,Qty,MPN,LCSC,Value,Footprint", "--group-by", "Value,MPN",
        "--exclude-dnp", "-o", str(raw), str(SCHEMATIC))
    designators = set()
    with raw.open(encoding="utf-8") as source, (OUT / "fuji75-bom.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(["Item #", "Designator", "Qty", "Mfg Part #", "LCSC Part #", "Description / Value", "Package/Footprint"])
        for item, row in enumerate(csv.DictReader(source), start=1):
            writer.writerow([item, row["Designator"], row["Qty"], row["MPN"], row["LCSC"], row["Value"],
                             row["Footprint"].split(":")[-1]])
            designators.update(expand(row["Designator"]))
    raw.unlink()
    return designators


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


def placement(designators):
    """PCBWay's CPL columns for every part in the BOM."""
    raw = OUT / "pos-raw.csv"
    cli("pcb", "export", "pos", "--side", "both", "--format", "csv", "--units", "mm", "--exclude-dnp", "-o", str(raw), str(PCB))
    placed = set()
    with raw.open(encoding="utf-8") as source, (OUT / "fuji75-cpl.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in csv.DictReader(source):
            if row["Ref"] not in designators:
                continue
            writer.writerow([row["Ref"], f'{float(row["PosX"]):.3f}mm', f'{float(row["PosY"]):.3f}mm',
                             "Top" if row["Side"] == "top" else "Bottom", f'{float(row["Rot"]):g}'])
            placed.add(row["Ref"])
    raw.unlink()
    return placed


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    gerbers()
    designators = bom()
    placed = placement(designators)
    missing = designators - placed
    if missing:
        sys.exit(f"In the BOM but not in the placement file: {', '.join(sorted(missing))}")
    print(f"Wrote {OUT}: {len(designators)} parts placed")


if __name__ == "__main__":
    main()
