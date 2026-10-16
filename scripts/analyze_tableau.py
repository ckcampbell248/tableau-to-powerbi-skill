#!/usr/bin/env python3
"""Bounded, offline Tableau structural inventory. NOT a migration engine."""

import argparse
from collections import Counter
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib


MAX_XML = 16 * 1024 * 1024
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_MEMBERS = 512
MAX_MEMBER = 32 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_RATIO = 100
MAX_NODES = 100_000
MAX_DEPTH = 64
MAX_REFERENCE_CANDIDATES = 32
CONNECTORS = {
    "sqlserver", "postgres", "mysql", "oracle", "snowflake", "bigquery",
    "redshift", "excel-direct", "textscan", "hyper", "dataengine",
    "federated", "tableau-server", "odbc", "genericjdbc", "sqlite",
}
DATATYPES = {"string", "integer", "real", "boolean", "date", "datetime", "spatial"}
FEATURE_TAGS = {
    "table-calc": "table_calculation",
    "table-calculation": "table_calculation",
    "filter": "filters",
    "group": "groups",
    "set": "sets",
    "hierarchy": "hierarchies",
    "join": "joins",
    "relationship": "relationships",
    "relation": "relations",
    "blend": "blending",
    "trend-line": "analytics",
    "forecast": "analytics",
    "reference-line": "analytics",
    "map": "maps",
    "story": "stories",
    "extension": "extensions",
    "device-layout": "device_layouts",
    "window": "window_metadata",
}
LOD = re.compile(r"\{\s*(?:FIXED|INCLUDE|EXCLUDE)\b", re.I)
TABLE_CALC = re.compile(
    r"\b(?:WINDOW_[A-Z_]+|RUNNING_[A-Z_]+|LOOKUP|INDEX|FIRST|LAST|SIZE|"
    r"RANK(?:_[A-Z_]+)?|TOTAL|PREVIOUS_VALUE)\s*\(", re.I
)


class AnalysisError(ValueError):
    """Safe diagnostic containing no source-controlled text."""


def bounded_read(stream, limit):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise AnalysisError("Input exceeds the configured read limit.")
    return data


def check_member(info):
    name = info.filename
    path = PurePosixPath(name)
    if (
        info.orig_filename != name or "\x00" in name or "\\" in name
        or ":" in name or path.is_absolute()
        or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
        or not name
    ):
        raise AnalysisError("Unsafe archive member path.")
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise AnalysisError("Archive contains a link or special file.")
    if info.flag_bits & (1 | 64):
        raise AnalysisError("Encrypted archive members are not supported.")
    if info.flag_bits & 32:
        raise AnalysisError("Patched ZIP members are not supported.")
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise AnalysisError("Unsupported archive compression.")
    if info.file_size > MAX_MEMBER:
        raise AnalysisError("Archive member exceeds the size limit.")
    if info.file_size / max(info.compress_size, 1) > MAX_RATIO:
        raise AnalysisError("Archive compression ratio exceeds the limit.")


def preflight_zip(data):
    """Bound central-directory parsing BEFORE ZipFile allocates ZipInfo objects."""
    offset = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if offset < 0 or offset + 22 > len(data):
        raise AnalysisError("Missing ZIP end record.")
    _, disk, central_disk, on_disk, count, size, start, comment = struct.unpack_from(
        "<4s4H2LH", data, offset
    )
    if offset + 22 + comment != len(data):
        raise AnalysisError("Unsupported ZIP end record or trailing data.")
    if disk or central_disk or on_disk != count:
        raise AnalysisError("Multi-disk ZIP archives are not supported.")
    if count == 65535 or size == 0xffffffff or start == 0xffffffff:
        raise AnalysisError("ZIP64 archives are not supported.")
    if count > MAX_MEMBERS:
        raise AnalysisError("Archive has too many members.")
    if start + size != offset:
        raise AnalysisError("Invalid or unsupported ZIP central directory.")
    cursor = start
    actual = 0
    while cursor < offset:
        if cursor + 46 > offset or data[cursor:cursor + 4] != b"PK\x01\x02":
            raise AnalysisError("Invalid ZIP central directory record.")
        name, extra, note = struct.unpack_from("<3H", data, cursor + 28)
        cursor += 46 + name + extra + note
        actual += 1
        if cursor > offset or actual > MAX_MEMBERS:
            raise AnalysisError("ZIP central directory limits exceeded.")
    if actual != count:
        raise AnalysisError("ZIP member count does not match the central directory.")


def load_workbook(path, member=None):
    suffix = path.suffix.lower()
    if suffix not in {".twb", ".twbx"}:
        raise AnalysisError("Expected a .twb or .twbx file.")
    with open(path, "rb", opener=lambda p, flags: os.open(p, flags | getattr(os, "O_NONBLOCK", 0))) as stream:
        size = os.fstat(stream.fileno()).st_size
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise AnalysisError("Input must be a regular file.")
        if suffix == ".twb":
            if member is not None:
                raise AnalysisError("--member applies only to TWBX input.")
            return bounded_read(stream, MAX_XML), "twb"
        if size > MAX_ARCHIVE:
            raise AnalysisError("Archive exceeds the size limit.")
        archive_data = bounded_read(stream, MAX_ARCHIVE)
        preflight_zip(archive_data)
        with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_MEMBERS:
                raise AnalysisError("Archive has too many members.")
            names = set()
            total = 0
            candidates = []
            for info in entries:
                check_member(info)
                key = info.filename.casefold()
                if key in names:
                    raise AnalysisError("Archive has duplicate or ambiguous member names.")
                names.add(key)
                total += info.file_size
                if total > MAX_TOTAL:
                    raise AnalysisError("Archive total uncompressed size exceeds the limit.")
                if not info.is_dir() and info.filename.lower().endswith(".twb"):
                    candidates.append(info)
            if member is None:
                if len(candidates) != 1:
                    raise AnalysisError("Archive must have exactly one workbook; select with --member.")
                chosen = candidates[0]
            else:
                matches = [info for info in candidates if info.filename == member]
                if len(matches) != 1:
                    raise AnalysisError("Selected workbook member was not found.")
                chosen = matches[0]
            if chosen.file_size > MAX_XML:
                raise AnalysisError("Workbook XML exceeds the size limit.")
            with archive.open(chosen) as workbook:
                data = bounded_read(workbook, MAX_XML)
            return data, "twbx"


def parse_xml(data):
    if len(data) > MAX_XML:
        raise AnalysisError("Workbook XML exceeds the size limit.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AnalysisError("Only UTF-8 workbook XML is supported.") from None
    declaration = re.match(r"\s*<\?xml\b[^?]*\?>", text, re.I)
    if declaration:
        encoding = re.search(r"encoding\s*=\s*['\"]([^'\"]+)['\"]", declaration[0], re.I)
        if encoding and encoding[1].lower() not in {"utf-8", "utf8", "us-ascii"}:
            raise AnalysisError("Only UTF-8 workbook XML is supported.")
    if "\x00" in text or re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        raise AnalysisError("DTD, entities and non-UTF-8 XML are forbidden.")
    parser = ET.XMLPullParser(events=("start", "end"))
    root = None
    nodes = depth = 0
    try:
        for offset in range(0, len(text), 4096):
            parser.feed(text[offset:offset + 4096])
            for event, element in parser.read_events():
                if event == "start":
                    if root is None:
                        root = element
                    nodes += 1
                    depth += 1
                    if nodes > MAX_NODES or depth > MAX_DEPTH:
                        raise AnalysisError("XML structural limits exceeded.")
                    if len(element.attrib) > 64 or any(len(v) > 65536 for v in element.attrib.values()):
                        raise AnalysisError("XML attribute limits exceeded.")
                else:
                    depth -= 1
        parser.close()
    except ET.ParseError:
        raise AnalysisError("Malformed workbook XML.") from None
    if root is None or root.tag != "workbook":
        raise AnalysisError("Expected an unnamespaced Tableau workbook root.")
    if any("}" in element.tag for element in root.iter()):
        raise AnalysisError("Namespaced workbook elements are not supported.")
    return root


def choice(value, allowed):
    return value if value in allowed else "unknown"


def integer(value):
    if value is not None and re.fullmatch(r"-?\d{1,8}", value):
        return int(value)
    return None


def analyze(data, source_format="twb"):
    root = parse_xml(data)
    objects = []
    object_counts = Counter()
    features = Counter()
    locations = {}

    def locate(element, path):
        locations[element] = path
        for index, child in enumerate(element, 1):
            locate(child, f"{path}/*[{index}]")

    locate(root, "/workbook")

    def add(element, kind, parent=None, **details):
        object_counts[kind] += 1
        obj = {
            "id": f"{kind}_{object_counts[kind]:04d}",
            "kind": kind,
            "locator": locations[element],
            "parent_id": parent,
            **details,
        }
        objects.append(obj)
        return obj["id"]

    datasource_names = {}
    field_names = {}
    for ds in root.findall("./datasources/datasource"):
        ds_id = add(
            ds, "datasource",
            connectors=sorted({
                choice(c.get("class"), CONNECTORS) for c in ds.iter("connection")
            }),
            is_parameter_container=ds.get("name") == "Parameters",
        )
        name = ds.get("name")
        if name:
            datasource_names.setdefault(name, []).append(ds_id)
        for col in ds.findall("./column"):
            calc = col.find("./calculation")
            is_parameter = col.get("param-domain-type") is not None or ds.get("name") == "Parameters"
            flags = []
            if calc is not None:
                expression = calc.get("formula", "") or calc.text or ""
                if LOD.search(expression):
                    flags.append("lod")
                if TABLE_CALC.search(expression):
                    flags.append("table_calculation")
            if is_parameter:
                features["parameters"] += 1
            field_id = add(
                col, "field", ds_id,
                datatype=choice(col.get("datatype"), DATATYPES),
                role=choice(col.get("role"), {"dimension", "measure"}),
                column_type=choice(col.get("type"), {"nominal", "ordinal", "quantitative"}),
                calculation=calc is not None,
                calculation_features=flags,
                parameter=is_parameter,
            )
            if col.get("name"):
                field_names.setdefault((ds_id, col.get("name")), []).append(field_id)

    worksheet_names = {}
    for sheet in root.findall("./worksheets/worksheet"):
        dependencies = []
        for dep in sheet.iter("datasource-dependencies"):
            ds_ids = datasource_names.get(dep.get("datasource"), [])
            columns = []
            for col in dep.findall("./column"):
                matches = field_names.get((ds_ids[0], col.get("name")), []) if len(ds_ids) == 1 else []
                columns.append({
                    "field_ids": matches[:MAX_REFERENCE_CANDIDATES],
                    "resolved": len(matches) == 1,
                    "candidate_count": len(matches) if len(ds_ids) == 1 else None,
                    "candidates_truncated": len(matches) > MAX_REFERENCE_CANDIDATES,
                    "datasource_unresolved": len(ds_ids) != 1,
                })
            dependencies.append({
                "datasource_ids": ds_ids[:MAX_REFERENCE_CANDIDATES],
                "datasource_candidate_count": len(ds_ids),
                "datasource_candidates_truncated": len(ds_ids) > MAX_REFERENCE_CANDIDATES,
                "resolved": len(ds_ids) == 1,
                "columns": columns,
            })
        ws_id = add(
            sheet, "worksheet",
            dependencies=dependencies,
            marks=sorted({
                choice(m.get("class"), {
                    "Automatic", "Bar", "Line", "Area", "Circle", "Square",
                    "Text", "Shape", "Pie", "Map", "GanttBar", "Polygon",
                }) for m in sheet.iter("mark")
            }),
            rows_present=any((e.text or "").strip() for e in sheet.iter("rows")),
            columns_present=any((e.text or "").strip() for e in sheet.iter("cols")),
            filter_count=sum(1 for _ in sheet.iter("filter")),
        )
        if sheet.get("name"):
            worksheet_names.setdefault(sheet.get("name"), []).append(ws_id)

    for dashboard in root.findall("./dashboards/dashboard"):
        size = dashboard.find("./size")
        dash_id = add(
            dashboard, "dashboard",
            size={k: integer(size.get(k)) for k in ("minwidth", "maxwidth", "minheight", "maxheight")}
            if size is not None else None,
        )
        for zone in dashboard.iter("zone"):
            ws_ids = worksheet_names.get(zone.get("name"), [])
            add(
                zone, "zone", dash_id,
                worksheet_ids=ws_ids[:MAX_REFERENCE_CANDIDATES],
                worksheet_candidate_count=len(ws_ids),
                worksheet_candidates_truncated=len(ws_ids) > MAX_REFERENCE_CANDIDATES,
                worksheet_reference_resolved=len(ws_ids) == 1,
                zone_type=choice(zone.get("type-v2"), {
                    "layout-basic", "layout-flow", "worksheet", "text", "bitmap",
                    "web", "filter", "paramctrl", "color", "size", "shape",
                }),
                bounds={k: integer(zone.get(k)) for k in ("x", "y", "w", "h")},
            )
    for action in root.iter("action"):
        add(action, "action")
        features["actions"] += 1
    for element in root.iter():
        if element.tag == "calculation":
            features["calculations"] += 1
            expression = element.get("formula", "") or element.text or ""
            if LOD.search(expression):
                features["lod"] += 1
            if TABLE_CALC.search(expression):
                features["table_calculation"] += 1
        if element.tag in FEATURE_TAGS:
            features[FEATURE_TAGS[element.tag]] += 1
        if element.tag == "relation":
            relation_type = element.get("type")
            if relation_type == "text":
                features["custom_sql"] += 1
            if relation_type in {"join", "union"}:
                features[relation_type + "s"] += 1
        if element.tag == "connection" and element.get("class") in {"hyper", "dataengine"}:
            features["extracts"] += 1
        if element.tag == "connection" and element.get("class") == "tableau-server":
            features["published_datasources"] += 1
        if element.tag == "column" and element.get("datatype") == "spatial":
            features["spatial_fields"] += 1
    known_top = {
        "datasources", "worksheets", "dashboards", "actions", "windows",
        "preferences", "document-format-change-manifest", "repository-location",
        "style", "thumbnails", "stories", "external", "map-sources",
    }
    unknown_top = sum(child.tag not in known_top for child in root)
    if unknown_top:
        features["unrecognized_top_level_sections"] = unknown_top
    inventory = {
        "format_version": 1,
        "source_format": source_format,
        "xml_element_count": len(locations),
        "privacy": "Names, labels, paths, connection attributes, SQL, formulas and data omitted.",
        "objects": objects,
        "features": dict(sorted(features.items())),
    }
    manifest = {
        "format_version": 1,
        "analysis_status": "inventoried_not_migrated",
        "migration_status": "not_started",
        "validation": {
            "xml": "passed_bounded_parse",
            "tmdl": "not_run", "pbir_schema": "not_run",
            "desktop_open_refresh": "not_run", "semantic_parity": "not_run",
        },
        "mappings": [{
            "source_id": obj["id"], "source_locator": obj["locator"],
            "source_kind": obj["kind"], "target": None,
            "status": "review_needed", "confidence": "unassessed",
            "reason": "Inventory only; inspect source locally and approve a target mapping.",
        } for obj in objects],
        "review_features": sorted(features),
        "feature_assessments": [{
            "feature": feature, "occurrences": features[feature],
            "status": "review_needed", "confidence": "unassessed",
            "reason": "Heuristic detection only; no semantic translation or validation.",
        } for feature in sorted(features)],
        "unsupported_automation": [
            "Calculation and custom SQL translation",
            "Extract data reading and connection/credential migration",
            "PBIP/TMDL/PBIR generation (agent-guided workflow only)",
            "Power BI Desktop execution and source/target parity validation",
        ],
        "limitations": [
            "No formulas, SQL, credentials, labels, paths or data are exported.",
            "Only structural heuristics; absence of a feature is not evidence of compatibility.",
            "No expression parsing, dependency completeness, connector validation or automatic conversion.",
            "No extracts read, external URLs fetched, arbitrary source content executed or binaries converted.",
            "Published sources, custom SQL, LOD, table calculations, parameters, actions, layout and unknown features require review.",
            "All source and target names must be reconciled privately using document-order locators.",
            "Ambiguous reference candidate arrays are capped at 32 with explicit counts/flags; fields under unresolved datasources are not expanded.",
        ],
    }
    return inventory, manifest


def write_results(directory, inventory, manifest):
    directory.mkdir(mode=0o700)
    for name, value in (("inventory.json", inventory), ("compatibility.json", manifest)):
        target = directory / name
        with open(target, "x", encoding="utf-8", opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=True)
            stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--member", help="Exact .twb member when a TWBX contains multiple workbooks.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory only; parent must exist.")
    args = parser.parse_args(argv)
    try:
        data, source_format = load_workbook(args.workbook, args.member)
        inventory, manifest = analyze(data, source_format)
        write_results(args.output_dir, inventory, manifest)
    except AnalysisError as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 2
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError,
            UnicodeDecodeError, NotImplementedError):
        print("Analysis failed: corrupt or invalid ZIP archive.", file=sys.stderr)
        return 2
    except OSError:
        print("Analysis failed: input/output unavailable, or output directory already exists. Partial output may remain.", file=sys.stderr)
        return 2
    print("Inventory written. Migration and Power BI validation have NOT been performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
