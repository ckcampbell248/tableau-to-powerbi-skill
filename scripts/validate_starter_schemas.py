#!/usr/bin/env python3
"""Optional ONLINE JSON Schema check for the fixed self-authored starter only.

Requires jsonschema >= 4.18. Does not read customer workbooks or validate TMDL.
"""

import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


SCHEMAS = {
    "Starter.pbip": "fabric/pbip/pbipProperties/1.0.0/schema.json",
    "Starter.SemanticModel/definition.pbism": "fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "Starter.Report/definition.pbir": "fabric/item/report/definitionProperties/2.0.0/schema.json",
    "Starter.Report/definition/version.json": "fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "Starter.Report/definition/report.json": "fabric/item/report/definition/report/3.0.0/schema.json",
    "Starter.Report/definition/pages/pages.json": "fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "Starter.Report/definition/pages/MigrationReview/page.json": "fabric/item/report/definition/page/2.0.0/schema.json",
}
PUBLIC_BASE = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"
ID_BASE = "https://developer.microsoft.com/json-schemas/"


def main():
    try:
        import jsonschema
        from referencing import Registry
    except ImportError:
        print("Optional dependency missing: install jsonschema>=4.18 in your local environment.", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1] / "templates" / "starter"
    for relative, schema_path in SCHEMAS.items():
        instance = json.loads((root / relative).read_text(encoding="utf-8"))
        if instance.get("$schema") != ID_BASE + schema_path:
            print("Unexpected starter schema identifier.", file=sys.stderr)
            return 2
        request = urllib.request.Request(PUBLIC_BASE + schema_path, headers={"User-Agent": "starter-schema-check"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                print("Public schema exceeds download limit.", file=sys.stderr)
                return 2
            schema = json.loads(data)
            if schema.get("$id") != instance["$schema"]:
                print("Public schema identifier mismatch.", file=sys.stderr)
                return 2
            jsonschema.Draft7Validator.check_schema(schema)
            # Only local/internal references resolve. Never follow arbitrary remote $refs.
            jsonschema.Draft7Validator(schema, registry=Registry()).validate(instance)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError,
                jsonschema.SchemaError, jsonschema.ValidationError) as exc:
            print(f"Schema check failed for {relative}: {type(exc).__name__}", file=sys.stderr)
            return 2
        print(f"PASS {relative} schema-sha256={hashlib.sha256(data).hexdigest()}")
    print("Seven JSON documents passed public schemas. TMDL and Desktop validation NOT performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
