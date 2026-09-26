#!/usr/bin/env python3
"""Uruchom niezmieniony listing, przekierowując jego historyczne /tmp do repo."""
from __future__ import annotations

import argparse
import builtins
import runpy
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--tmp-dir", type=Path, required=True)
    args = parser.parse_args()
    args.tmp_dir.mkdir(parents=True, exist_ok=True)
    source = args.source.resolve()
    real_open = builtins.open

    def redirected_open(file, *open_args, **open_kwargs):
        if isinstance(file, (str, bytes)):
            text = file.decode() if isinstance(file, bytes) else file
            normalized = text.replace("\\", "/")
            if normalized.startswith("/tmp/"):
                file = args.tmp_dir / Path(normalized).name
        return real_open(file, *open_args, **open_kwargs)

    builtins.open = redirected_open
    try:
        runpy.run_path(str(source), run_name="__main__")
    finally:
        builtins.open = real_open
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
