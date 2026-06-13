from pathlib import Path

# Fedora repository base URL (no trailing slash).
# If set to the placeholder below, the program will prompt for it at runtime.
FEDORA_URL = "YOUR_FEDORA_URL"

# Internet Archive CSV: rename pattern applied to the output filename.
# Replaces IA_RENAME_FROM with IA_RENAME_TO in the generated filename.
# Set both to None to skip renaming.
IA_RENAME_FROM = "box"
IA_RENAME_TO   = "NAL_14_merrigan_455-"

# Delimiter used between columns in output CSVs.
# Standard comma keeps the file recognisable to Excel / LibreOffice without
# any manual import-wizard configuration.
COL_SEP = ","

# Delimiter used between multiple values within a single cell.
# In Omeka Classic CSV Import set "Element delimiter" to the same character.
VAL_SEP = "|"

# File extension appended to the identifier to build the sideload filename.
# Change to ".jpg", ".pdf", etc. to match your actual object files.
SIDELOAD_EXT = ".tiff"
