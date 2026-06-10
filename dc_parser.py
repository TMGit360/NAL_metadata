"""Parse OAI-DC (Dublin Core) XML files into the shared fields dict format."""

import xml.etree.ElementTree as ET

DC_NS  = "http://purl.org/dc/elements/1.1/"
OAI_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"


def parse_dc_file(path):
    """Yield parsed records from a Dublin Core XML file."""
    tree = ET.parse(path)
    root = tree.getroot()

    # May be wrapped in OAI-PMH ListRecords or a bare oai_dc:dc element
    dc_elements = root.findall(f".//{{{OAI_NS}}}dc") or [root]

    for dc_el in dc_elements:
        yield _parse_dc_element(dc_el)


def _text(el):
    return el.text.strip() if el.text and el.text.strip() else None


def _parse_dc_element(dc_el):
    def collect(local_name):
        return [
            t for el in dc_el.findall(f"{{{DC_NS}}}{local_name}")
            if (t := _text(el))
        ]

    return {
        "title":       collect("title"),
        "subject":     collect("subject"),
        "description": collect("description"),
        "creator":     collect("creator"),
        "contributor": collect("contributor"),
        "source":      collect("source"),
        "publisher":   collect("publisher"),
        "date":        collect("date"),
        "rights":      collect("rights"),
        "relation":    collect("relation"),
        "format":      collect("format"),
        "language":    collect("language"),
        "type":        collect("type"),
        "identifier":  collect("identifier"),
        "toc":         [],
        "tags":        [],
        "box":         None,
        "folder":      None,
    }
