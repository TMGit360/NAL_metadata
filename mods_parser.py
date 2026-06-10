"""Shared MODS XML parsing helpers."""

import xml.etree.ElementTree as ET
from pathlib import Path

MODS_NS = "http://www.loc.gov/mods/v3"


def _tag(name):
    return f"{{{MODS_NS}}}{name}"


def _text(element, path):
    """Return stripped text at XPath path, or None."""
    node = element.find(path, {"m": MODS_NS})
    if node is not None and node.text:
        return node.text.strip()
    return None


def _texts(element, path):
    """Return list of stripped texts for all matching nodes."""
    return [
        n.text.strip()
        for n in element.findall(path, {"m": MODS_NS})
        if n.text and n.text.strip()
    ]


def find_xml_files(directory):
    """Yield XML files from a directory, with or without .xml extension."""
    directory = Path(directory)
    seen = set()
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".xml" or path.suffix == "":
            # Quick check: does it look like XML?
            try:
                with open(path, "rb") as f:
                    snippet = f.read(64)
                if b"<" in snippet:
                    seen.add(path)
                    yield path
            except OSError:
                continue


def parse_mods(xml_path):
    """Parse a MODS XML file and return a dict of Dublin Core + extra fields."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # Handle modsCollection wrapper
    if root.tag != _tag("mods"):
        root = root.find(f"{{{MODS_NS}}}mods") or root

    ns = {"m": MODS_NS}

    # ------------------------------------------------------------------ Title
    title = _text(root, "m:titleInfo/m:title")
    subtitle = _text(root, "m:titleInfo/m:subTitle")
    if title and subtitle:
        title = f"{title}: {subtitle}"

    # ----------------------------------------------------------------- Names
    creators = []
    for name_el in root.findall("m:name", ns):
        # Collect name parts by type; skip date/termsOfAddress parts
        full = given = family = None
        untyped_parts = []
        for part in name_el.findall("m:namePart", ns):
            t = part.get("type")
            text = part.text.strip().rstrip(",") if part.text else None
            if not text:
                continue
            if t == "given":
                given = text
            elif t == "family":
                family = text
            elif t is None:
                untyped_parts.append(text)
            # type="termsOfAddress" and type="date" intentionally skipped

        if untyped_parts:
            full = " ".join(untyped_parts)
        elif family or given:
            full = ", ".join(filter(None, [family, given]))

        roles = [
            rt.text.strip()
            for rt in name_el.findall("m:role/m:roleTerm", ns)
            if rt.text and rt.text.strip()
        ]
        role = "; ".join(roles) if roles else None

        if full:
            creators.append(f"{full} ({role})" if role else full)

    # ------------------------------------------------------------ Description
    descriptions = []
    for el in root.findall("m:abstract", ns) + root.findall("m:note", ns):
        if el.text:
            text = el.text.replace("\r", " ").replace("\n", " ").strip()
            if text:
                descriptions.append(text)

    # --------------------------------------------------------------- Source
    sources = _texts(root, "m:location/m:holdingSimple/m:copyInformation/m:shelfLocator")

    # ------------------------------------------------------------- Publisher
    # MODS 3.6+ may use originInfo/agent/namePart instead of originInfo/publisher
    publishers = _texts(root, "m:originInfo/m:publisher")
    if not publishers:
        for agent_el in root.findall("m:originInfo/m:agent", ns):
            role_el = agent_el.find("m:role/m:roleTerm", ns)
            role = role_el.text.strip().lower() if (role_el is not None and role_el.text) else ""
            if role in ("publisher", ""):
                np = agent_el.find("m:namePart", ns)
                if np is not None and np.text:
                    publishers.append(np.text.strip().rstrip(","))

    # ----------------------------------------------------------------- Dates
    date_paths = [
        "m:originInfo/m:dateIssued",
        "m:originInfo/m:dateCreated",
        "m:originInfo/m:dateCaptured",
        "m:originInfo/m:copyrightDate",
        "m:originInfo/m:dateOther",
    ]
    dates = []
    for path in date_paths:
        dates.extend(_texts(root, path))

    # --------------------------------------------------------------- Rights
    rights = _texts(root, "m:accessCondition")

    # --------------------------------------------------------------- Format
    formats = (
        _texts(root, "m:physicalDescription/m:form")
        + _texts(root, "m:physicalDescription/m:extent")
        + _texts(root, "m:physicalDescription/m:note")
    )

    # ------------------------------------------------------------- Language
    # Prefer human-readable text terms; fall back to code values
    languages = _texts(root, "m:language/m:languageTerm[@type='text']")
    if not languages:
        languages = [
            lt.text.strip()
            for lt in root.findall("m:language/m:languageTerm", ns)
            if lt.text and lt.text.strip()
        ]

    # ----------------------------------------------------------------- Type
    types = _texts(root, "m:genre")

    # ------------------------------------------------------------- Identifier
    # Prefer LCCN; skip invalid identifiers; fall back to first valid one
    identifier = None
    for id_el in root.findall("m:identifier", ns):
        if id_el.get("invalid"):
            continue
        if id_el.get("type") == "lccn" and id_el.text:
            identifier = id_el.text.strip()
            break
    if not identifier:
        for id_el in root.findall("m:identifier", ns):
            if not id_el.get("invalid") and id_el.text and id_el.text.strip():
                identifier = id_el.text.strip()
                break
    if not identifier:
        ri = root.find("m:recordInfo/m:recordIdentifier", ns)
        if ri is not None and ri.text:
            identifier = ri.text.strip()

    box_link = folder_link = None
    if identifier:
        parts = identifier.split("-")
        if len(parts) >= 2:
            box_link = "-".join(parts[:2])
        if len(parts) >= 3:
            folder_link = "-".join(parts[:3])

    # --------------------------------------------------------------- Subjects
    # Each <subject> element is one heading; join its children with " -- "
    subjects = []
    for subj_el in root.findall("m:subject", ns):
        parts = []
        for child in subj_el:
            tag = child.tag.split("}")[-1]  # strip namespace
            if tag in ("geographicCode",):  # skip control-coded fields
                continue
            if tag == "name":
                for np in child.findall("m:namePart", ns):
                    if np.get("type") is None and np.text:
                        parts.append(np.text.strip().rstrip(","))
            elif tag == "titleInfo":
                t = _text(child, "m:title")
                if t:
                    parts.append(t)
            elif child.text and child.text.strip():
                parts.append(child.text.strip().rstrip(".,"))
        heading = " -- ".join(parts)
        if heading:
            subjects.append(heading)

    subjects = list(dict.fromkeys(subjects))  # deduplicate, preserve order

    # --------------------------------------------------------------- TOC
    toc_parts = []
    for el in root.findall("m:tableOfContents", ns):
        if el.text:
            # Em-dashes used as section separators become multi-value delimiter
            for part in el.text.replace("—", "--").split("--"):
                part = part.strip()
                if part:
                    toc_parts.append(part)

    # --------------------------------------------------------------- Tags
    tags = set()
    subj_str = " ".join(subjects)
    if "Natural" in subj_str:
        tags.add("organic")

    return {
        "title":       title,
        "subject":     subjects,
        "description": descriptions,
        "creator":     creators,
        "source":      sources,
        "publisher":   publishers,
        "date":        dates,
        "rights":      rights,
        "format":      formats,
        "language":    languages,
        "type":        types,
        "identifier":  identifier,
        "toc":         toc_parts,
        "tags":        sorted(tags),
        "box":         box_link,
        "folder":      folder_link,
    }
