#!/usr/bin/env python3
"""Validate the public registry and build registry/index.json.

Each registry file must be a TBF document whose root matches its directory:
exercises → exercise, metrics → metric, programs → program.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATORS = ROOT / "tbf" / "validators"
sys.path.insert(0, str(VALIDATORS))

import validate  # noqa: E402

REGISTRY = ROOT / "registry"
SCHEMA = ROOT / "tbf" / "schema" / "1.0" / "document.schema.json"
SECTIONS = {
    "exercises": "exercise",
    "metrics": "metric",
    "programs": "program",
}


def title_of(root: dict) -> str:
    return root.get("title") or root.get("name") or root["id"]


def main() -> int:
    schema = validate.load_schema(SCHEMA)
    seen: set[tuple[str, str]] = set()
    index: list[dict] = []
    failed = False

    for folder, expected_type in SECTIONS.items():
        directory = REGISTRY / folder
        for path in sorted(directory.glob("*.tbf.json")):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
                validate.validate_document(document, schema)
                root = document["root"]
                if root["type"] != expected_type:
                    raise validate.ValidationError(
                        f"root type must be {expected_type}, found {root['type']}"
                    )
                key = (root["type"], root["id"])
                if key in seen:
                    raise validate.ValidationError(f"duplicate registry id {key}")
                seen.add(key)
                root_object = next(
                    obj
                    for obj in document["objects"]
                    if obj["type"] == root["type"] and obj["id"] == root["id"]
                )
                index.append(
                    {
                        "type": root["type"],
                        "id": root["id"],
                        "title": title_of(root_object),
                        "checksum": root_object["checksum"],
                        "file": str(path.relative_to(ROOT)),
                    }
                )
            except (OSError, json.JSONDecodeError, validate.ValidationError) as error:
                failed = True
                print(f"FAIL {path}: {error}", file=sys.stderr)

    index.sort(key=lambda item: (item["type"], item["title"].casefold()))
    output = REGISTRY / "index.json"
    output.write_text(
        json.dumps({"tbf": "1.0", "objects": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(index)} registry entries to {output}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
