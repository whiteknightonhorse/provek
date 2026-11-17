#!/usr/bin/env python3
"""T-DEP-05 (D-86) - the site is built only from an install that matches the lockfile.

The door (`scripts/push.sh`, step 6/9) builds the site with the `node_modules` already on this host;
CI installs from the lockfile with `npm ci`. Nothing ran `npm ci` here after 2026-10-28, so when
Dependabot's auto-merged bumps moved `web/package-lock.json` (genlayer-js rc.2 -> rc.3, vite 8.3.5 ->
8.3.8, ...) the door kept building a site from the old packages and no gate said so. This program
compares, for every package the lockfile names, the lockfile's `version` with the `version` of the
`package.json` actually installed at that path.

  exit 0  every package is installed at the version the lockfile names
  exit 1  drift: one or more packages differ or are missing (a missing OPTIONAL one is not drift)
  exit 2  not_measured, in three different lines:
            check_did_not_run  - `<root>/node_modules` is absent
            unreadable         - the lockfile, or an installed package.json, could not be read
            nothing_qualified  - the lockfile names no package (N = 0 is never a match)

EXTRANEOUS PACKAGES ARE NOT COMPARED. A directory under `node_modules` that the lockfile does not
name is not read: this checks "what the lockfile names is installed as named", not "nothing else is
installed" (`npm ci` removes the extras; this does not claim to).

The door does not install. It refuses and prints the command: `cd web && npm ci --ignore-scripts`
(`--ignore-scripts` is safe here: the only package of the lockfile with an install script is the
darwin-only `fsevents`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOOR_COMMAND = "cd web && npm ci --ignore-scripts"


def _unreadable(path: Path, why: object) -> int:
    print(f"not_measured: unreadable - {path}: {why}")
    return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT / "web",
                    help="the directory holding package-lock.json and node_modules (default: web)")
    args = ap.parse_args(argv)
    root: Path = args.root

    lock_path = root / "package-lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        packages = lock["packages"]
        if not isinstance(packages, dict):
            raise TypeError("`packages` is not an object")
    except (OSError, ValueError, KeyError, TypeError) as e:
        return _unreadable(lock_path, f"{type(e).__name__}: {e}")

    named = {k: v for k, v in packages.items() if k != ""}
    if not named:
        print("not_measured: nothing_qualified - the lockfile names no package")
        return 2

    if not (root / "node_modules").is_dir():
        print(f"not_measured: check_did_not_run - {root}/node_modules is absent")
        return 2

    drift: list[str] = []
    optional_absent = 0
    for key in sorted(named):
        entry = named[key]
        want = entry.get("version") if isinstance(entry, dict) else None
        if not isinstance(want, str):
            return _unreadable(lock_path, f"{key} names no version")
        pkg_json = root / key / "package.json"
        try:
            have = json.loads(pkg_json.read_text(encoding="utf-8")).get("version")
        except FileNotFoundError:
            if entry.get("optional") is True:
                optional_absent += 1
            else:
                drift.append(f"{key} lock={want} installed=missing")
            continue
        except (OSError, ValueError, AttributeError) as e:
            return _unreadable(pkg_json, f"{type(e).__name__}: {e}")
        if not isinstance(have, str):
            return _unreadable(pkg_json, "no version field")
        if have != want:
            drift.append(f"{key} lock={want} installed={have}")

    if drift:
        print(f"drift: {len(drift)} of {len(named)}")
        for line in drift:
            print(line)
        print(f"Door: {DOOR_COMMAND}")
        return 1
    print(f"match: {len(named)} packages installed as the lockfile names them ({optional_absent} optional absent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
