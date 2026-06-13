#!/usr/bin/env python3
"""nalmd — NAL metadata toolkit CLI."""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import config

# File that remembers the last directory you used
_STATE_FILE = Path(__file__).parent / ".nalmd_state.json"


# ── Tab completion for filesystem paths (Linux/Mac only) ─────────────────────

try:
    import readline

    def _path_completer(text, state):
        matches = glob.glob(os.path.expanduser(text) + "*")
        matches = [m + "/" if os.path.isdir(m) else m for m in matches]
        return matches[state] if state < len(matches) else None

    readline.set_completer(_path_completer)
    readline.set_completer_delims(" \t\n;")
    readline.parse_and_bind("tab: complete")
    _TAB_COMPLETION = True
except ImportError:
    _TAB_COMPLETION = False  # Windows — tab completion unavailable


# ── Last-used directory ───────────────────────────────────────────────────────

def _load_last_dir():
    try:
        return Path(json.loads(_STATE_FILE.read_text())["last_dir"])
    except Exception:
        return None

def _save_last_dir(path: Path):
    try:
        _STATE_FILE.write_text(json.dumps({"last_dir": str(path)}))
    except Exception:
        pass


# ── Prompts ───────────────────────────────────────────────────────────────────

def prompt_input_dir(verb="process"):
    last = _load_last_dir()
    hint = f"  (last used: {last})" if last and last.is_dir() else ""
    tab_tip = "  Tip: press Tab to autocomplete paths." if _TAB_COMPLETION else ""
    if tab_tip or hint:
        print(f"{tab_tip}{hint}")
    while True:
        answer = input("Input folder: ").strip()
        if answer.lower() in ("quit", "q", "exit"):
            return None
        if not answer and last and last.is_dir():
            answer = str(last)
            print(f"  Using: {answer}")
        if not answer:
            continue
        path = Path(answer).expanduser().resolve()
        if path.is_dir():
            _save_last_dir(path)
            return path
        print(f"  '{answer}' is not a valid folder. Try again.")


def prompt_input_file(label="File"):
    if _TAB_COMPLETION:
        print("  Tip: press Tab to autocomplete paths.")
    while True:
        answer = input(f"{label}: ").strip()
        if answer.lower() in ("quit", "q", "exit"):
            return None
        if not answer:
            continue
        path = Path(answer).expanduser().resolve()
        if path.is_file():
            return path
        print(f"  '{answer}' not found. Try again.")


def prompt_output_dir(input_path: Path, suffix="output"):
    suggested = input_path.parent / f"{input_path.name}_{suffix}"
    cwd = Path.cwd()
    print(f"\n  Where should the CSV be saved?")
    print(f"  [Enter] Next to your input:   {suggested}")
    print(f"  [1]     Current terminal dir: {cwd}")
    print(f"  [path]  Type any folder path")
    while True:
        answer = input("  Choice: ").strip()
        if answer.lower() in ("quit", "q", "exit"):
            return None
        if answer == "":
            return suggested
        if answer == "1":
            return cwd
        path = Path(answer).expanduser().resolve()
        return path


def prompt_objects_dir():
    """Ask for an optional separate folder containing object files."""
    print("\n  Object files folder (images, videos, documents, etc.)")
    print("  [Enter] Same as metadata folder")
    print("  [path]  Type a different folder path")
    answer = input("  Objects folder: ").strip()
    if not answer or answer.lower() in ("quit", "q", "exit"):
        return None
    path = Path(answer).expanduser().resolve()
    if path.is_dir():
        return path
    print(f"  '{answer}' is not a valid folder — using metadata folder instead.")
    return None


def prompt_fedora_url():
    if config.FEDORA_URL and config.FEDORA_URL != "YOUR_FEDORA_URL":
        return config.FEDORA_URL
    while True:
        url = input("  Fedora base URL (e.g. https://repo.example.org/fedora): ").strip()
        if url:
            return url.rstrip("/")
        print("  A Fedora URL is required.")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_convert():
    from convert_all import convert_directory
    print("\nConvert a folder of metadata files to an Omeka CSV.")
    print("Handles MODS XML, MARCXML, MARC21 binary, and Dublin Core automatically.\n")
    target = prompt_input_dir()
    if not target:
        return
    objects_dir = prompt_objects_dir()
    output_dir = prompt_output_dir(target, suffix="omeka")
    if output_dir:
        print()
        convert_directory(target, output_dir, objects_dir=objects_dir)

def cmd_omeka():
    from mods_to_omeka import mods_to_omeka
    print("\nConvert a folder of MODS XML files to an Omeka CSV.\n")
    target = prompt_input_dir()
    if not target:
        return
    objects_dir = prompt_objects_dir()
    output_dir = prompt_output_dir(target, suffix="omeka")
    if output_dir:
        print()
        mods_to_omeka(target, output_dir, objects_dir=objects_dir)

def cmd_marc():
    from marc_to_omeka import marc_to_omeka
    print("\nConvert a single MARC21 binary (.mrc) file to an Omeka CSV.\n")
    mrc_file = prompt_input_file("MARC21 .mrc file")
    if not mrc_file:
        return
    objects_dir = prompt_objects_dir()
    output_dir = prompt_output_dir(mrc_file, suffix="omeka")
    if output_dir:
        print()
        marc_to_omeka(mrc_file, output_dir, objects_dir=objects_dir)

def cmd_iacsv():
    from mods_to_ia import mods_to_ia
    print("\nConvert a folder of MODS XML files to an Internet Archive batch CSV.\n")
    target = prompt_input_dir()
    if not target:
        return
    output_dir = prompt_output_dir(target, suffix="ia_csv")
    if output_dir:
        print()
        mods_to_ia(target, output_dir)

def cmd_rename():
    from rename_by_id import rename_by_id
    print("\nRename MODS XML files using each record's <identifier> value.\n")
    target = prompt_input_dir()
    if target:
        print()
        rename_by_id(target)

def cmd_getmods():
    from download_mods import get_mods
    print("\nDownload MODS records from a Fedora repository.\n")
    pid_file = prompt_input_file("Text file of Fedora PIDs")
    if not pid_file:
        return
    output_dir = prompt_output_dir(pid_file, suffix="mods")
    if not output_dir:
        return
    fedora_url = prompt_fedora_url()
    print()
    get_mods(pid_file, output_dir, fedora_url)


# ── Interactive menu ──────────────────────────────────────────────────────────

MENU = [
    ("Convert a folder of files to Omeka CSV  (MODS, MARCXML, MARC binary, Dublin Core)", cmd_convert),
    ("Convert a MODS XML folder to Omeka CSV",                                            cmd_omeka),
    ("Convert a MARC21 binary (.mrc) file to Omeka CSV",                                  cmd_marc),
    ("Convert a MODS XML folder to Internet Archive CSV",                                  cmd_iacsv),
    ("Rename MODS XML files by identifier",                                                cmd_rename),
    ("Download MODS records from Fedora",                                                  cmd_getmods),
]

def interactive_menu():
    print("\n╔══════════════════════════════════════╗")
    print("║       NAL Metadata Toolkit           ║")
    print("╚══════════════════════════════════════╝\n")
    for i, (label, _) in enumerate(MENU, 1):
        print(f"  {i}) {label}")
    print(f"  q) Quit\n")
    while True:
        choice = input("Choose an option: ").strip().lower()
        if choice in ("q", "quit", "exit"):
            print("Goodbye.")
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            _, fn = MENU[int(choice) - 1]
            fn()
            return
        print("  Please enter a number from the menu.")


# ── Entry point ───────────────────────────────────────────────────────────────

CLI_COMMANDS = {
    "convert": cmd_convert,
    "omeka":   cmd_omeka,
    "marc":    cmd_marc,
    "iacsv":   cmd_iacsv,
    "rename":  cmd_rename,
    "getmods": cmd_getmods,
}

def main():
    # No arguments → show the interactive menu
    if len(sys.argv) == 1:
        interactive_menu()
        return

    parser = argparse.ArgumentParser(
        prog="nalmd",
        description="NAL metadata toolkit — run with no arguments for the interactive menu.",
    )
    parser.add_argument(
        "command",
        choices=CLI_COMMANDS.keys(),
        metavar="COMMAND",
        help=f"One of: {', '.join(CLI_COMMANDS)}",
    )
    args = parser.parse_args()
    CLI_COMMANDS[args.command]()


if __name__ == "__main__":
    main()
