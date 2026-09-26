#!/usr/bin/env python3
"""Uruchom niezmieniony kod rozdziału 7 z kompatybilnymi ścieżkami danych."""
from __future__ import annotations

import argparse
import builtins
import os
import runpy
import urllib.request
from pathlib import Path

RESULT_NAMES = {"real_results.json", "patch_results.json"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    args = parser.parse_args()
    args.run_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    source = args.source.resolve()
    before = source.read_bytes()

    real_open = builtins.open
    real_exists = os.path.exists
    real_makedirs = os.makedirs
    real_urlretrieve = urllib.request.urlretrieve

    def mapped(value):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return value
        text = os.fsdecode(value).replace("\\", "/")
        if not text.startswith("/tmp/"):
            return value
        relative = Path(text[5:])
        if relative.name in RESULT_NAMES:
            return args.run_dir / relative.name
        return args.cache_dir / relative

    def redirected_open(file, *open_args, **open_kwargs):
        return real_open(mapped(file), *open_args, **open_kwargs)

    def redirected_exists(path):
        return real_exists(mapped(path))

    def redirected_makedirs(name, *make_args, **make_kwargs):
        mode = make_args[0] if make_args else make_kwargs.get("mode", 0o777)
        exist_ok = make_kwargs.get("exist_ok", False)
        return Path(mapped(name)).mkdir(mode=mode, parents=True, exist_ok=exist_ok)

    def compatible_urlretrieve(url, filename=None, *url_args, **url_kwargs):
        target = mapped(filename) if filename is not None else filename
        if target is not None:
            Path(target).parent.mkdir(parents=True, exist_ok=True)
        candidates = [url]
        leaf = url.rsplit("/", 1)[-1]
        if "fashion-mnist" in url:
            candidates += [
                "https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/" + leaf,
            ]
        elif "mnist" in url:
            candidates += [
                "https://storage.googleapis.com/cvdf-datasets/mnist/" + leaf,
                "https://ossci-datasets.s3.amazonaws.com/mnist/" + leaf,
            ]
        last = None
        for candidate in dict.fromkeys(candidates):
            try:
                return real_urlretrieve(candidate, target, *url_args, **url_kwargs)
            except Exception as exc:  # zgodność transportu; ostatni wyjątek wraca do użytkownika
                last = exc
        raise last

    builtins.open = redirected_open
    os.path.exists = redirected_exists
    os.makedirs = redirected_makedirs
    urllib.request.urlretrieve = compatible_urlretrieve
    try:
        runpy.run_path(str(source), run_name="__main__")
    finally:
        builtins.open = real_open
        os.path.exists = real_exists
        os.makedirs = real_makedirs
        urllib.request.urlretrieve = real_urlretrieve

    if source.read_bytes() != before:
        raise RuntimeError("Historyczne źródło zostało zmienione podczas wykonania")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
