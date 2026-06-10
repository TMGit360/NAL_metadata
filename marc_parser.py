"""Minimal MARC21 binary record parser. No external dependencies."""


def parse_marc21_file(path):
    """Yield parsed records from a MARC21 binary file."""
    with open(path, "rb") as f:
        data = f.read()

    pos = 0
    while pos < len(data):
        if pos + 5 > len(data):
            break
        try:
            rec_len = int(data[pos:pos + 5])
        except ValueError:
            break
        record_data = data[pos:pos + rec_len]
        yield _parse_record(record_data)
        pos += rec_len


def _parse_record(data):
    leader = data[:24].decode("utf-8", errors="replace")
    try:
        base = int(leader[12:17])
    except ValueError:
        return {"leader": leader, "fields": {}}

    dir_bytes = data[24:base - 1]  # -1 skips the field terminator byte
    entries = []
    for i in range(0, len(dir_bytes), 12):
        chunk = dir_bytes[i:i + 12]
        if len(chunk) < 12:
            break
        try:
            tag = chunk[0:3].decode("utf-8")
            length = int(chunk[3:7])
            offset = int(chunk[7:12])
            entries.append((tag, length, offset))
        except (ValueError, UnicodeDecodeError):
            continue

    fields = {}
    for tag, length, offset in entries:
        raw = data[base + offset: base + offset + length - 1]  # strip field terminator
        if tag < "010":
            # Control field: plain text, no indicators or subfields
            value = raw.decode("utf-8", errors="replace")
            fields.setdefault(tag, []).append({"data": value})
        else:
            if len(raw) < 2:
                continue
            ind1 = chr(raw[0])
            ind2 = chr(raw[1])
            subfields = []
            for chunk in raw[2:].split(b"\x1f")[1:]:
                if chunk:
                    code = chr(chunk[0])
                    value = chunk[1:].decode("utf-8", errors="replace")
                    subfields.append((code, value))
            fields.setdefault(tag, []).append(
                {"ind1": ind1, "ind2": ind2, "subfields": subfields}
            )

    return {"leader": leader, "fields": fields}


def get_subfield(field, code):
    """Return first matching subfield value, or None."""
    for c, v in field.get("subfields", []):
        if c == code:
            return v.strip().rstrip(".,/;:")
    return None


def get_subfields(field, *codes):
    """Return all values for any of the given subfield codes."""
    return [
        v.strip().rstrip(".,/;:")
        for c, v in field.get("subfields", [])
        if c in codes and v.strip()
    ]
