# NAL Metadata Toolkit

A command-line tool for converting library metadata files into CSVs for batch import into [Omeka Classic](https://omeka.org/classic/) or [Internet Archive](https://archive.org/). No installation required beyond Python 3.

---

## What it does

Point the tool at a folder of metadata files and it produces a ready-to-import CSV. It handles four input formats automatically:

| Format | Example |
|---|---|
| MODS XML | `.xml` files from a Fedora repository |
| MARCXML | `.xml` files in the MARC21 Slim schema |
| MARC21 binary | `.mrc` files |
| Dublin Core XML | OAI-DC formatted `.xml` files |

You can mix formats in the same folder — the tool detects each file's format by reading its contents, not its extension.

---

## Requirements

- Python 3.8 or later
- No external packages — everything uses the Python standard library

---

## Getting the files

Download or clone this repository to anywhere on your computer:

```bash
git clone https://github.com/your-org/NAL_metadata.git
```

Or download a ZIP from the repository page and unzip it wherever you like — your Documents folder, Desktop, or a dedicated tools folder all work fine.

---

## Setup

### Quick install (Linux/Mac)

Run the included install script once:

```bash
bash /path/to/NAL_metadata-master/install.sh
```

This does two things automatically:
- Adds a `nalmd` alias to your shell so you can type `nalmd` from any terminal instead of the full path
- Installs a launcher in GNOME so the tool appears in Activities search (Linux only)

After running it, open a new terminal (or run `source ~/.bashrc`) and you can start the tool with just:

```bash
nalmd
```

### Manual setup (any platform)

If you'd rather not run the install script, just call the script directly by its full path:

```bash
python3 /path/to/NAL_metadata-master/nalmd.py
```

### Windows

The tool works on Windows with one limitation: Tab key autocompletion at path prompts is not available (it requires a library that Windows doesn't include with Python by default). Everything else works normally. Run it from Command Prompt or PowerShell:

```
python C:\path\to\NAL_metadata-master\nalmd.py
```

### Optional: edit config.py

Two settings in `config.py` are worth changing if they apply to you:

- **`FEDORA_URL`** — set this if you use the `getmods` command to download records from a Fedora repository. If you leave it blank, the tool will ask you each time.
- **`IA_RENAME_FROM` / `IA_RENAME_TO`** — controls how the Internet Archive CSV output file is named. Change these to match your collection's naming convention, or set both to `None` to skip renaming.

---

## How to run it

Open a terminal and type:

```bash
python3 /path/to/nalmd.py
```

Replace `/path/to/nalmd.py` with the actual location on your computer — for example:

```bash
python3 /home/you/Documents/NAL_metadata-master/nalmd.py
```

A menu appears:

```
╔══════════════════════════════════════╗
║       NAL Metadata Toolkit           ║
╚══════════════════════════════════════╝

  1) Convert a folder of files to Omeka CSV  (MODS, MARCXML, MARC binary, Dublin Core)
  2) Convert a MODS XML folder to Omeka CSV
  3) Convert a MARC21 binary (.mrc) file to Omeka CSV
  4) Convert a MODS XML folder to Internet Archive CSV
  5) Rename MODS XML files by identifier
  6) Download MODS records from Fedora

  q) Quit

Choose an option:
```

Pick a number and the tool walks you through the rest. **Press Tab at any path prompt to autocomplete folder and file names.** After your first run, the tool remembers the last folder you used and offers it as the default.

**Choosing where to save:**

```
  Where should the CSV be saved?
  [Enter] Next to your input:   /home/you/records/batch1_omeka
  [1]     Current terminal dir: /home/you
  [path]  Type any folder path
```

Press **Enter** to save next to your input files, **1** to save in the current terminal directory, or type any path.

---

## Commands

| Command | What it does |
|---|---|
| `convert` | **Start here.** Converts a folder of mixed-format files into a single Omeka CSV |
| `omeka` | Converts a folder of MODS XML files into an Omeka CSV |
| `marc` | Converts a single MARC21 binary (`.mrc`) file into an Omeka CSV |
| `iacsv` | Converts a folder of MODS XML files into an Internet Archive batch upload CSV |
| `rename` | Renames MODS XML files in a folder using each record's `<identifier>` value |
| `getmods` | Downloads MODS records from a Fedora repository using a text file of PIDs |

---

## Importing into Omeka

When using **CSV Import** in Omeka Classic, set the following options:

| Setting | Value |
|---|---|
| Column delimiter | `\|` (pipe) |
| Element delimiter | `^` (caret) |
| Tag delimiter | `^` (caret) |
| File encoding | UTF-8 |

The column headers in the CSV (e.g. `Dublin Core:Title`) map automatically to Omeka's Dublin Core fields — no manual field mapping needed.

---

## Notes

- **Duplicate records:** If the same item appears in multiple formats in the same folder, it will produce duplicate rows in the CSV. The tool does this intentionally — deduplication is up to you before importing.
- **Identifiers:** For MODS files, the tool prefers the LCCN when multiple identifiers are present, and skips any marked as invalid.
- **Geocoding:** Not supported. The Omeka CSV Import plugin cannot import location data for the Geolocation plugin via CSV.
