"""Convert a directory of MODS XML files to an Omeka CSV Import CSV."""

import csv
from pathlib import Path

from config import COL_SEP, VAL_SEP
from mods_parser import parse_mods, find_xml_files

HEADERS = [
    "Dublin Core:Title",
    "Dublin Core:Subject",
    "Dublin Core:Description",
    "Dublin Core:Contributor",
    "Dublin Core:Source",
    "Dublin Core:Publisher",
    "Dublin Core:Date",
    "Dublin Core:Rights",
    "Dublin Core:Format",
    "Dublin Core:Language",
    "Dublin Core:Type",
    "Dublin Core:Identifier",
    "Item Type Metadata:Table of Contents",
    "tags",
    "Item Type Metadata:Box",
    "Item Type Metadata:Folder",
]


def _join(values):
    return VAL_SEP.join(v for v in values if v)


def mods_to_omeka(target_dir: Path, output_dir: Path):
    target_dir = Path(target_dir).resolve()
    output_dir = Path(output_dir).resolve()
    xml_files = list(find_xml_files(target_dir))
    if not xml_files:
        print(f"No XML files found in {target_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{target_dir.name}_omeka.csv"

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=COL_SEP, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(HEADERS)

        for xml_path in xml_files:
            print(f"  Processing {xml_path.name}")
            try:
                d = parse_mods(xml_path)
            except Exception as e:
                print(f"  ERROR parsing {xml_path.name}: {e}")
                continue

            writer.writerow([
                d["title"] or "",
                _join(d["subject"]),
                _join(d["description"]),
                _join(d["creator"]),
                _join(d["source"]),
                _join(d["publisher"]),
                _join(d["date"]),
                _join(d["rights"]),
                _join(d["format"]),
                _join(d["language"]),
                _join(d["type"]),
                d["identifier"] or "",
                _join(d["toc"]),
                _join(d["tags"]),
                d["box"] or "",
                d["folder"] or "",
            ])
            print(f"  Added {d['identifier'] or xml_path.name}")

    print(f"\nWrote {len(xml_files)} records to {out_path}")
    return out_path
