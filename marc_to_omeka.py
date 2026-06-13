"""Convert a MARC21 binary file (.mrc) to an Omeka CSV Import CSV."""

import csv
from pathlib import Path

from config import COL_SEP, VAL_SEP
from marc_parser import parse_marc21_file, get_subfield, get_subfields

_METADATA_EXTS = {".xml", ".mrc", ".csv", ".txt", ".log", ".py", ".rb", ".json"}


def _find_object_file(directory: Path, identifier: str) -> str:
    """Return the filename of the object file matching the identifier, or the bare identifier."""
    if not identifier:
        return ""
    if directory:
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
]

# MARC subject tags → DC:Subject
SUBJECT_TAGS = {"600", "610", "611", "630", "650", "651", "653"}

# MARC genre/form tags → DC:Type
TYPE_TAGS = {"655", "336"}


def _join(values):
    return VAL_SEP.join(v for v in values if v)


def _name_string(field):
    """Build a display string from a name field (1xx/7xx)."""
    parts = get_subfields(field, "a", "b", "c")
    name = " ".join(parts)
    role_parts = get_subfields(field, "e")
    role = "; ".join(role_parts) if role_parts else None
    return f"{name} ({role})" if role else name


def marc_record_to_dc(fields):
    """Map a parsed MARC record's fields dict to a Dublin Core dict."""

    # ------------------------------------------------------------------ Title
    title = None
    for f in fields.get("245", []):
        main = get_subfield(f, "a") or ""
        sub = get_subfield(f, "b")
        medium = get_subfield(f, "h")  # e.g. "[graphic]" — strip it
        title = f"{main}: {sub}" if sub else main
        break

    # ----------------------------------------------------------- Creator (1xx)
    creators = []
    for tag in ("100", "110", "111"):
        for f in fields.get(tag, []):
            s = _name_string(f)
            if s:
                creators.append(s)

    # ------------------------------------------------------- Contributor (7xx)
    contributors = []
    for tag in ("700", "710", "711"):
        for f in fields.get(tag, []):
            s = _name_string(f)
            if s:
                contributors.append(s)

    # --------------------------------------------------------------- Subject
    subjects = []
    seen_subjects = set()
    for tag in sorted(SUBJECT_TAGS):
        for f in fields.get(tag, []):
            parts = get_subfields(f, "a", "b", "v", "x", "y", "z")
            if parts:
                heading = " -- ".join(parts)
                if heading not in seen_subjects:
                    subjects.append(heading)
                    seen_subjects.add(heading)

    # ------------------------------------------------------------ Description
    descriptions = []
    for f in fields.get("520", []):   # summary/abstract
        v = get_subfield(f, "a")
        if v:
            descriptions.append(v)
    for f in fields.get("500", []):   # general notes
        v = get_subfield(f, "a")
        if v:
            descriptions.append(v)
    for f in fields.get("541", []):   # acquisition notes
        parts = get_subfields(f, "a", "c", "d")
        if parts:
            descriptions.append(" ".join(parts))

    # --------------------------------------------------------------- Source
    sources = []
    for f in fields.get("852", []):
        parts = get_subfields(f, "a", "b", "c")
        if parts:
            sources.append(", ".join(parts))

    # ------------------------------------------------------------- Publisher
    publishers = []
    for tag in ("260", "264"):
        for f in fields.get(tag, []):
            v = get_subfield(f, "b")
            if v:
                publishers.append(v)

    # ----------------------------------------------------------------- Date
    dates = []
    for tag in ("260", "264"):
        for f in fields.get(tag, []):
            v = get_subfield(f, "c")
            if v:
                dates.append(v)
    # Fallback to 008 fixed field positions 7-10 (year)
    if not dates:
        for f in fields.get("008", []):
            year = f.get("data", "")[7:11].strip()
            if year and year != "    ":
                dates.append(year)

    # --------------------------------------------------------------- Rights
    rights = []
    for tag in ("540", "542"):
        for f in fields.get(tag, []):
            v = get_subfield(f, "a")
            if v:
                rights.append(v)

    # --------------------------------------------------------------- Relation
    relations = []
    for f in fields.get("773", []):
        v = get_subfield(f, "t")
        if v:
            relations.append(v)

    # --------------------------------------------------------------- Format
    formats = []
    for f in fields.get("300", []):
        # Preserve original subfield text including ISBD punctuation
        raw_parts = [v for c, v in f.get("subfields", []) if c in ("a", "b", "c") and v.strip()]
        if raw_parts:
            formats.append(" ".join(raw_parts))

    # ------------------------------------------------------------- Language
    languages = []
    for f in fields.get("041", []):
        languages.extend(get_subfields(f, "a"))
    if not languages:
        for f in fields.get("008", []):
            lang = f.get("data", "")[35:38].strip()
            if lang and lang != "   ":
                languages.append(lang)

    # ----------------------------------------------------------------- Type
    types = []
    for tag in sorted(TYPE_TAGS):
        for f in fields.get(tag, []):
            v = get_subfield(f, "a")
            if v:
                types.append(v)

    # ------------------------------------------------------------- Identifier
    identifiers = []
    for f in fields.get("001", []):
        if f.get("data"):
            identifiers.append(f["data"].strip())
    for f in fields.get("010", []):
        v = get_subfield(f, "a")
        if v:
            identifiers.append(v.strip())

    # --------------------------------------------------------------- TOC
    toc_parts = []
    for f in fields.get("505", []):
        v = get_subfield(f, "a")
        if v:
            for part in v.replace("—", "--").split("--"):
                part = part.strip()
                if part:
                    toc_parts.append(part)

    # --------------------------------------------------------------- Tags
    tags = set()
    subj_str = " ".join(subjects)
    if "Natural" in subj_str:
        tags.add("organic")

    return {
        "title":       title or "",
        "subject":     subjects,
        "description": descriptions,
        "creator":     creators,
        "contributor": contributors,
        "source":      sources,
        "publisher":   publishers,
        "date":        dates,
        "rights":      rights,
        "relation":    relations,
        "format":      formats,
        "language":    languages,
        "type":        types,
        "identifier":  identifiers,
        "toc":         toc_parts,
        "tags":        sorted(tags),
    }


def marc_to_omeka(mrc_path: Path, output_dir: Path):
    mrc_path = Path(mrc_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{mrc_path.stem}_omeka.csv"

    records = list(parse_marc21_file(mrc_path))
    if not records:
        print(f"No records found in {mrc_path}")
        return

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=COL_SEP, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(HEADERS)

        for i, record in enumerate(records, 1):
            d = marc_record_to_dc(record["fields"])
            identifier_str = _join(d["identifier"])
            first_id = d["identifier"][0] if d["identifier"] else ""
            types = d.get("type", [])
            writer.writerow([
                _find_object_file(mrc_path.parent, first_id),
                d["title"],
                _join(d["subject"]),
                _join(d["description"]),
                _join(d["creator"]),
                _join(d["contributor"]),
                _join(d["source"]),
                _join(d["publisher"]),
                _join(d["date"]),
                _join(d["rights"]),
                _join(d["relation"]),
                _join(d["format"]),
                _join(d["language"]),
                _join(types),
                types[0] if types else "",
                identifier_str,
                _join(d["toc"]),
                _join(d["tags"]),
            ])
            print(f"  Added record {i}: {identifier_str or '(no identifier)'}")

    print(f"\nWrote {len(records)} records to {out_path}")
    print(f"  Omeka CSV Import — set 'Element delimiter' to:  {VAL_SEP}")
    return out_path
