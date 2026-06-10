"""Detect metadata format of a file by content inspection."""

from pathlib import Path


MARC_BINARY   = "marc_binary"
MARC_XML      = "marcxml"
MODS_XML      = "mods"
DC_XML        = "dublin_core"
UNKNOWN       = "unknown"


def detect_format(path: Path) -> str:
    """Return a format constant for the given file."""
    path = Path(path)
    try:
        # MARC21 binary: starts with 5 ASCII digits (record length)
        with open(path, "rb") as f:
            header = f.read(256)

        # MARC21 binary: 5-digit length header; terminator may be at end of file
        if header[:5].isdigit():
            with open(path, "rb") as f:
                f.seek(-4, 2)
                tail = f.read()
            if b"\x1d" in header or b"\x1d" in tail:
                return MARC_BINARY

        # XML-based: sniff the namespace
        text = header.decode("utf-8", errors="replace").replace("\n", " ")

        if "loc.gov/MARC21/slim" in text:
            return MARC_XML

        if "loc.gov/mods/v3" in text:
            return MODS_XML

        if any(ns in text for ns in (
            "oai_dc",
            "dublincore",
            "purl.org/dc/",
            "dublincore.org",
        )):
            return DC_XML

        # If it looks like XML but namespace wasn't in the first 256 bytes,
        # read more and try again
        if text.lstrip().startswith("<"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                full = f.read(4096)
            if "loc.gov/MARC21/slim" in full:
                return MARC_XML
            if "loc.gov/mods/v3" in full:
                return MODS_XML
            if any(ns in full for ns in ("oai_dc", "dublincore", "purl.org/dc/")):
                return DC_XML

    except OSError:
        pass

    return UNKNOWN
