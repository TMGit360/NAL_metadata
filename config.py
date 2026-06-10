from pathlib import Path

# Fedora repository base URL (no trailing slash).
# If set to the placeholder below, the program will prompt for it at runtime.
FEDORA_URL = "YOUR_FEDORA_URL"

# Internet Archive CSV: rename pattern applied to the output filename.
# Replaces IA_RENAME_FROM with IA_RENAME_TO in the generated filename.
# Set both to None to skip renaming.
IA_RENAME_FROM = "box"
IA_RENAME_TO   = "NAL_14_merrigan_455-"

# Delimiter used between columns in output CSVs
COL_SEP = "|"

# Delimiter used between multiple values within a single cell
VAL_SEP = "^"
