"""Convert a directory of MODS XML files to an Internet Archive batch CSV."""

import csv
import re
from pathlib import Path

from config import IA_RENAME_FROM, IA_RENAME_TO, COL_SEP
from mods_parser import parse_mods, find_xml_files

IA_HEADERS = ["identifier", "filename_seed", "creator", "title", "date", "subject", "access_note"]

ACCESS_NOTE = (
    "Please note that these files are not available for download at archive.org. "
    "After further processing, they will be available through "
    "http://specialcollections.nal.usda.gov/."
)


def _normalize_date(raw):
    """Return a 4-digit year string from a variety of date formats."""
    if not raw:
        return raw
    raw = raw.replace(",", " ").replace("?", "").strip()
    m = re.match(r"(\d{4})", raw)
    if m:
        return m.group(1)
    m = re.match(r"([a-zA-Z]+)\s+\d{1,2}\s+(\d{4})", raw)
    if m:
        return m.group(2)
    return raw


def mods_to_ia(target_dir: Path, output_dir: Path):
    target_dir = Path(target_dir).resolve()
    output_dir = Path(output_dir).resolve()
    xml_files = list(find_xml_files(target_dir))
    if not xml_files:
        print(f"No XML files found in {target_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    stem = target_dir.name
    raw_path = output_dir / f"{stem}.csv"
    fixed_stem = stem.replace(IA_RENAME_FROM, IA_RENAME_TO) if (IA_RENAME_FROM and IA_RENAME_TO) else stem
    fixed_dir = output_dir / "fixed"
    fixed_dir.mkdir(exist_ok=True)
    fixed_path = fixed_dir / f"{fixed_stem}.csv"

    rows = []
    for xml_path in xml_files:
        print(f"  Processing {xml_path.name}")
        try:
            d = parse_mods(xml_path)
        except Exception as e:
            print(f"  ERROR parsing {xml_path.name}: {e}")
            continue

        identifier = d["identifier"] or xml_path.stem
        creator    = ";".join(d["creator"])
        title      = d["title"] or ""
        date       = _normalize_date(";".join(d["date"]))
        subject    = ";".join(d["subject"])
        rows.append([identifier, identifier, creator, title, date, subject, ACCESS_NOTE])
        print(f"  Added {identifier}")

    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=COL_SEP, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(IA_HEADERS)
        writer.writerows(rows)

    with open(fixed_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=COL_SEP, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(IA_HEADERS)
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} records to {raw_path}")
    print(f"Wrote fixed copy to {fixed_path}")
    return fixed_path
