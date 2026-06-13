"""Convert a directory of mixed metadata files to a single Omeka CSV."""

import csv
from pathlib import Path

from config import COL_SEP, VAL_SEP
from format_detector import detect_format, MARC_BINARY, MARC_XML, MODS_XML, DC_XML, UNKNOWN

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
    "Dublin Core:Creator",
    "Dublin Core:Contributor",
    "Dublin Core:Source",
    "Dublin Core:Publisher",
    "Dublin Core:Date",
    "Dublin Core:Rights",
    "Dublin Core:Relation",
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
    if isinstance(values, list):
        return VAL_SEP.join(v for v in values if v)
    return values or ""


def _records_from_file(path):
    """Yield normalised DC dicts from a file, regardless of source format."""
    fmt = detect_format(path)

    if fmt == MARC_BINARY:
        from marc_parser import parse_marc21_file
        from marc_to_omeka import marc_record_to_dc
        for rec in parse_marc21_file(path):
            d = marc_record_to_dc(rec["fields"])
            d.setdefault("box", None)
            d.setdefault("folder", None)
            yield fmt, d

    elif fmt == MARC_XML:
        from marcxml_parser import parse_marcxml_file
        from marc_to_omeka import marc_record_to_dc
        for rec in parse_marcxml_file(path):
            d = marc_record_to_dc(rec["fields"])
            d.setdefault("box", None)
            d.setdefault("folder", None)
            yield fmt, d

    elif fmt == MODS_XML:
        from mods_parser import parse_mods
        d = parse_mods(path)
        yield fmt, d

    elif fmt == DC_XML:
        from dc_parser import parse_dc_file
        for d in parse_dc_file(path):
            yield fmt, d

    else:
        yield UNKNOWN, None


def _is_candidate(path: Path) -> bool:
    """Skip files that are clearly not metadata (existing CSVs, etc.)."""
    return path.suffix.lower() not in (".csv", ".txt", ".log", ".py", ".rb")


def convert_directory(source_dir: Path, output_dir: Path, output_name: str = None, objects_dir: Path = None):
    source_dir = Path(source_dir).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    out_name = output_name or f"{source_dir.name}_omeka.csv"
    if not out_name.endswith(".csv"):
        out_name += "_omeka.csv"
    out_path = output_dir / out_name

    search_dir = Path(objects_dir).resolve() if objects_dir else source_dir
    candidates = sorted(f for f in source_dir.iterdir() if f.is_file() and _is_candidate(f))

    if not candidates:
        print(f"No metadata files found in {source_dir}")
        return

    total = 0
    skipped = 0
    format_counts = {}

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=COL_SEP, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(HEADERS)

        for path in candidates:
            print(f"\n  {path.name}")
            found_any = False
            for fmt, d in _records_from_file(path):
                if fmt == UNKNOWN or d is None:
                    print(f"    Unrecognised format — skipped")
                    skipped += 1
                    break
                format_counts[fmt] = format_counts.get(fmt, 0) + 1
                identifier_raw = d.get("identifier")
                if isinstance(identifier_raw, list):
                    identifier = _join(identifier_raw)
                    first_id = identifier_raw[0] if identifier_raw else ""
                else:
                    identifier = identifier_raw or ""
                    first_id = identifier
                print(f"    [{fmt}] → {identifier or '(no identifier)'}")
                types = d.get("type", [])
                writer.writerow([
                    _find_object_file(search_dir, path.stem),
                    _join(d.get("title") or ""),
                    _join(d.get("subject", [])),
                    _join(d.get("description", [])),
                    _join(d.get("creator", [])),
                    _join(d.get("contributor", [])),
                    _join(d.get("source", [])),
                    _join(d.get("publisher", [])),
                    _join(d.get("date", [])),
                    _join(d.get("rights", [])),
                    _join(d.get("relation", [])),
                    _join(d.get("format", [])),
                    _join(d.get("language", [])),
                    _join(types),
                    types[0] if types else "",
                    identifier,
                    _join(d.get("toc", [])),
                    _join(d.get("tags", [])),
                    d.get("box") or "",
                    d.get("folder") or "",
                ])
                total += 1
                found_any = True
            if not found_any and skipped == 0:
                skipped += 1

    print(f"\n{'='*50}")
    print(f"Output: {out_path}")
    print(f"Records written: {total}")
    if skipped:
        print(f"Files skipped:   {skipped}")
    for fmt, count in sorted(format_counts.items()):
        print(f"  {fmt}: {count} record(s)")
    print(f"\n  Omeka CSV Import — set 'Element delimiter' to:  {VAL_SEP}")
    return out_path
