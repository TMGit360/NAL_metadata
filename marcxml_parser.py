"""Parse MARCXML files into the same fields dict as marc_parser.py."""

import xml.etree.ElementTree as ET

MARC_NS = "http://www.loc.gov/MARC21/slim"
MNS = {"m": MARC_NS}


def parse_marcxml_file(path):
    """Yield parsed records from a MARCXML file (single record or collection)."""
    tree = ET.parse(path)
    root = tree.getroot()

    # Root may be a single <record> or a <collection> wrapping many
    if root.tag == f"{{{MARC_NS}}}record":
        yield _parse_record_element(root)
    else:
        for rec_el in root.findall("m:record", MNS):
            yield _parse_record_element(rec_el)


def _parse_record_element(rec_el):
    leader_el = rec_el.find("m:leader", MNS)
    leader = leader_el.text.strip() if (leader_el is not None and leader_el.text) else ""

    fields = {}

    for cf in rec_el.findall("m:controlfield", MNS):
        tag = cf.get("tag", "")
        value = cf.text.strip() if cf.text else ""
        fields.setdefault(tag, []).append({"data": value})

    for df in rec_el.findall("m:datafield", MNS):
        tag  = df.get("tag", "")
        ind1 = df.get("ind1", " ")
        ind2 = df.get("ind2", " ")
        subfields = []
        for sf in df.findall("m:subfield", MNS):
            code  = sf.get("code", "")
            value = sf.text.strip() if sf.text else ""
            if code and value:
                subfields.append((code, value))
        fields.setdefault(tag, []).append(
            {"ind1": ind1, "ind2": ind2, "subfields": subfields}
        )

    return {"leader": leader, "fields": fields}
