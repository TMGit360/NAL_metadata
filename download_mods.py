"""Fetch MODS datastreams from a Fedora repository given a text file of PIDs."""

import urllib.request
from pathlib import Path


def get_mods(pid_file: Path, output_dir: Path, fedora_url: str):
    pid_file = Path(pid_file).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pids = [line.strip() for line in pid_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    for pid in pids:
        print(f"Retrieving {pid}...")
        pid_clean = pid.replace("info:fedora/", "").replace(":", "-").replace("/", "_")
        url = f"{fedora_url.rstrip('/')}/{pid_clean}/datastreams/MODS/content"
        print(f"  {url}")
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read()
            out_path = output_dir / f"{pid_clean}_mods.xml"
            out_path.write_bytes(data)
            print(f"  Saved {out_path.name}")
        except Exception as e:
            print(f"  ERROR fetching {pid}: {e}")
