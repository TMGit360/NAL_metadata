"""Convert a directory of MODS XML files to an Omeka CSV Import CSV."""

import csv
from pathlib import Path

from config import COL_SEP, VAL_SEP
from mods_parser import parse_mods, find_xml_files

_METADATA_EXTS = {".xml", ".mrc", ".csv", ".txt", ".log", ".py", ".rb", ".json"}


def _find_object_file(directory: Path, identifier: str) -> str:
    """Return the filename of the object file matching the identifier, or the bare identifier."""
    if not identifier:
        return ""
    for match in sorted(directory.glob(f"{identifier}.*")):
        if match.suffix.lower() not in _METADATA_EXTS:
            return match.name
    return identifier

HEADERS = [
    "sideload",
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
    "item_type_name",
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
        writer = csv.writer(f, delimiter=COL_SEP, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(HEADERS)

        for xml_path in xml_files:
            print(f"  Processing {xml_path.name}")
            try:
                d = parse_mods(xml_path)
            except Exception as e:
                print(f"  ERROR parsing {xml_path.name}: {e}")
                continue

            types = d.get("type", [])
            writer.writerow([
                _find_object_file(target_dir, d["identifier"] or ""),
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
                _join(types),
                types[0] if types else "",
                d["identifier"] or "",
                _join(d["toc"]),
                _join(d["tags"]),
                d["box"] or "",
                d["folder"] or "",
            ])
            print(f"  Added {d['identifier'] or xml_path.name}")

    print(f"\nWrote {len(xml_files)} records to {out_path}")
    print(f"  Omeka CSV Import — set 'Element delimiter' to:  {VAL_SEP}")
    return out_path
