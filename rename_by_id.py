"""Rename MODS XML files in a directory by their <identifier> value."""

import xml.etree.ElementTree as ET
from pathlib import Path

MODS_NS = {"m": "http://www.loc.gov/mods/v3"}


def rename_by_id(target_dir: Path):
    target_dir = Path(target_dir).resolve()

    for xml_path in sorted(target_dir.glob("*.xml")):
        print(f"Checking {xml_path.name}")
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            id_el = root.find("m:identifier", MODS_NS)
            if id_el is None or not id_el.text:
                print(f"  No identifier found, skipping.")
                continue
            identifier = id_el.text.strip()
            new_name = f"{identifier}_{xml_path.stem}_mods.xml"
            new_path = xml_path.parent / new_name
            xml_path.rename(new_path)
            print(f"  Renamed to {new_name}")
        except Exception as e:
            print(f"  ERROR: {e}")
