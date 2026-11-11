#!/usr/bin/env python3
"""Validate TwinBells Format 1.0 documents.

Checks JSON Schema, root resolution, references, duplicate IDs and checksums.
Use --write-checksums to fill or refresh checksums in example files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import FormatChecker
except ImportError as error:  # pragma: no cover - CLI dependency guard
    raise SystemExit(
        "Missing dependency: pip install -r requirements.txt"
    ) from error


HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE.parent / "schema" / "1.0" / "document.schema.json"
OBJECT_TYPES = ("metric", "exercise", "program", "journal")


class ValidationError(Exception):
    pass


def canonical_json(value: Any) -> bytes:
    """Canonical JSON for checksums: sorted keys, compact, UTF-8, no floats."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def ref_checksum(checksums: dict[tuple[str, str], str], type_name: str, object_id: str) -> dict[str, str]:
    key = (type_name, object_id)
    if key not in checksums:
        raise ValidationError(
            f"missing dependency {type_name}:{object_id}"
        )
    return {"type": type_name, "checksum": checksums[key]}


def semantic_projection(
    obj: dict[str, Any],
    checksums: dict[tuple[str, str], str],
) -> dict[str, Any]:
    type_name = obj["type"]

    if type_name == "metric":
        return {
            "type": "metric",
            "name": obj["name"],
            "description": obj.get("description", ""),
            "kind": obj["kind"],
            "unit": obj["unit"],
            "loadRole": obj["loadRole"],
        }

    if type_name == "exercise":
        metrics = []
        for metric in obj["metrics"]:
            metrics.append(
                {
                    "metric": ref_checksum(checksums, "metric", metric["metric"]),
                    "position": metric["position"],
                    "required": metric["required"],
                }
            )
        return {
            "type": "exercise",
            "name": obj["name"],
            "description": obj.get("description", ""),
            "restSeconds": obj["restSeconds"],
            "metrics": metrics,
        }

    if type_name == "program":
        group_index = {
            group["id"]: index
            for index, group in enumerate(obj.get("groups", []))
        }
        groups = [
            {
                "rounds": group["rounds"],
                "order": group["order"],
            }
            for group in obj.get("groups", [])
        ]
        items = []
        for item in obj["items"]:
            items.append(
                {
                    "exercise": ref_checksum(
                        checksums, "exercise", item["exercise"]
                    ),
                    "position": item["position"],
                    "plannedSetCount": item["plannedSetCount"],
                    "group": (
                        None
                        if item.get("group") is None
                        else group_index[item["group"]]
                    ),
                    "groupPosition": item["groupPosition"],
                }
            )
        return {
            "type": "program",
            "name": obj["name"],
            "description": obj.get("description", ""),
            "restBetweenExercisesSeconds": obj["restBetweenExercisesSeconds"],
            "groups": groups,
            "items": items,
        }

    if type_name == "journal":
        workouts = []
        for workout in obj["workouts"]:
            workout_copy = copy.deepcopy(workout)
            workout_copy.pop("id", None)
            for workout_exercise in workout_copy.get("exercises", []):
                workout_exercise["exercise"] = ref_checksum(
                    checksums, "exercise", workout_exercise["exercise"]
                )
                for set_value in workout_exercise.get("sets", []):
                    for value in set_value.get("values", []):
                        value["metric"] = ref_checksum(
                            checksums, "metric", value["metric"]
                        )
            workouts.append(workout_copy)

        measurements = copy.deepcopy(obj["measurements"])
        measure_index = {
            measure_type["id"]: index
            for index, measure_type in enumerate(measurements["types"])
        }
        measurements["types"] = [
            {
                "name": measure_type["name"],
                "unit": measure_type.get("unit", ""),
            }
            for measure_type in measurements["types"]
        ]
        for day in measurements["days"]:
            for value in day["values"]:
                value["type"] = measure_index[value["type"]]

        return {
            "type": "journal",
            "title": obj["title"],
            "personName": obj.get("personName", ""),
            "workouts": workouts,
            "measurements": measurements,
        }

    raise ValidationError(f"unknown object type: {type_name}")


def collect_objects(document: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for obj in document["objects"]:
        key = (obj["type"], obj["id"])
        if key in seen:
            raise ValidationError(f"duplicate object {key[0]}:{key[1]}")
        seen[key] = obj
    root = document["root"]
    root_key = (root["type"], root["id"])
    if root_key not in seen:
        raise ValidationError(f"root object not found: {root['type']}:{root['id']}")
    return seen


def check_references(
    document: dict[str, Any],
    objects: dict[tuple[str, str], dict[str, Any]],
) -> None:
    object_keys = set(objects)
    for (type_name, object_id), obj in objects.items():
        if type_name == "exercise":
            for metric in obj["metrics"]:
                key = ("metric", metric["metric"])
                if key not in object_keys:
                    raise ValidationError(
                        f"exercise:{object_id} references missing metric:{metric['metric']}"
                    )
        elif type_name == "program":
            group_ids = {group["id"] for group in obj.get("groups", [])}
            for item in obj["items"]:
                key = ("exercise", item["exercise"])
                if key not in object_keys:
                    raise ValidationError(
                        f"program:{object_id} references missing exercise:{item['exercise']}"
                    )
                if item.get("group") is not None and item["group"] not in group_ids:
                    raise ValidationError(
                        f"program:{object_id} references missing group:{item['group']}"
                    )
        elif type_name == "journal":
            measure_types = {item["id"] for item in obj["measurements"]["types"]}
            for workout in obj["workouts"]:
                for workout_exercise in workout["exercises"]:
                    key = ("exercise", workout_exercise["exercise"])
                    if key not in object_keys:
                        raise ValidationError(
                            f"journal:{object_id} references missing exercise:"
                            f"{workout_exercise['exercise']}"
                        )
                    for set_value in workout_exercise.get("sets", []):
                        for value in set_value.get("values", []):
                            metric_key = ("metric", value["metric"])
                            if metric_key not in object_keys:
                                raise ValidationError(
                                    f"journal:{object_id} references missing metric:"
                                    f"{value['metric']}"
                                )
            for day in obj["measurements"]["days"]:
                for value in day["values"]:
                    if value["type"] not in measure_types:
                        raise ValidationError(
                            f"journal:{object_id} references missing measurement type:"
                            f"{value['type']}"
                        )


def calculate_checksums(
    document: dict[str, Any],
    objects: dict[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str], str]:
    checksums: dict[tuple[str, str], str] = {}
    for type_name in OBJECT_TYPES:
        for (obj_type, object_id), obj in objects.items():
            if obj_type != type_name:
                continue
            checksums[(obj_type, object_id)] = sha256(
                semantic_projection(obj, checksums)
            )
    return checksums


def validate_document(document: dict[str, Any], schema: dict[str, Any]) -> dict[tuple[str, str], str]:
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        lines = []
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "document"
            lines.append(f"{location}: {error.message}")
        raise ValidationError("\n".join(lines))

    objects = collect_objects(document)
    check_references(document, objects)
    checksums = calculate_checksums(document, objects)

    for key, obj in objects.items():
        stored = obj.get("checksum")
        expected = checksums[key]
        if stored != expected:
            raise ValidationError(
                f"{key[0]}:{key[1]} checksum mismatch: "
                f"expected {expected}, found {stored}"
            )
    return checksums


def write_checksums(document: dict[str, Any]) -> None:
    objects = collect_objects(document)
    check_references(document, objects)
    checksums = calculate_checksums(document, objects)
    for obj in document["objects"]:
        obj["checksum"] = checksums[(obj["type"], obj["id"])]


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--write-checksums",
        action="store_true",
        help="Fill or refresh checksums in the provided files",
    )
    args = parser.parse_args()

    schema = load_schema(args.schema)
    failed = False

    for path in iter_files(args.files):
        try:
            with path.open("r", encoding="utf-8") as stream:
                document = json.load(stream)

            if args.write_checksums:
                write_checksums(document)
                with path.open("w", encoding="utf-8") as stream:
                    json.dump(document, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")

            validate_document(document, schema)
            print(f"OK   {path}")
        except ValidationError as error:
            failed = True
            print(f"FAIL {path}\n{error}", file=sys.stderr)
        except (OSError, json.JSONDecodeError) as error:
            failed = True
            print(f"FAIL {path}: {error}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
