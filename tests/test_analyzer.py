import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid
import warnings
import zipfile

from scripts import analyze_tableau as analyzer


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "minimal.twb"


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.work = ROOT / "tests" / ".runs" / uuid.uuid4().hex
        self.work.mkdir(parents=True)
        self.xml = FIXTURE.read_bytes()

    def tearDown(self):
        shutil.rmtree(self.work)
        try:
            self.work.parent.rmdir()
        except OSError:
            pass  # Another test process may still own a child directory.

    def package(self, members=None, compression=zipfile.ZIP_DEFLATED):
        target = self.work / "synthetic.twbx"
        with zipfile.ZipFile(target, "w", compression=compression) as archive:
            for name, data in members or [("Workbook.twb", self.xml)]:
                archive.writestr(name, data)
        return target

    def test_structural_inventory(self):
        inventory, manifest = analyzer.analyze(self.xml)
        kinds = [o["kind"] for o in inventory["objects"]]
        self.assertEqual(kinds.count("datasource"), 2)
        self.assertEqual(kinds.count("field"), 6)
        self.assertEqual(kinds.count("worksheet"), 1)
        self.assertEqual(kinds.count("dashboard"), 1)
        self.assertEqual(kinds.count("zone"), 2)
        self.assertEqual(kinds.count("action"), 1)
        self.assertEqual(inventory["features"]["lod"], 1)
        self.assertEqual(inventory["features"]["table_calculation"], 1)
        self.assertEqual(inventory["features"]["custom_sql"], 1)
        self.assertEqual(inventory["features"]["parameters"], 1)
        self.assertEqual(manifest["migration_status"], "not_started")
        self.assertTrue(all(m["target"] is None and m["status"] == "review_needed"
                            for m in manifest["mappings"]))
        self.assertTrue(all(f["status"] == "review_needed" for f in manifest["feature_assessments"]))

    def test_no_sensitive_or_arbitrary_strings(self):
        output = json.dumps(analyzer.analyze(self.xml))
        for value in ("SECRET_", "example.invalid", "Regional Sales", "[Sales]",
                      "RUNNING_SUM", "SELECT *", "Synthetic Sales", "Threshold"):
            self.assertNotIn(value, output)

    def test_unknown_attributes_and_names_are_not_exported(self):
        xml = b'<workbook SECRET="secret"><datasources><datasource name="secret"><connection class="secret" arbitrary="secret"/><column name="secret" datatype="secret" role="secret"/></datasource></datasources><secret/></workbook>'
        inventory, _ = analyzer.analyze(xml)
        self.assertNotIn("secret", json.dumps(inventory))
        self.assertEqual(inventory["features"]["unrecognized_top_level_sections"], 1)
        self.assertEqual(inventory["objects"][0]["connectors"], ["unknown"])

    def test_deterministic(self):
        self.assertEqual(analyzer.analyze(self.xml), analyzer.analyze(self.xml))

    def test_document_order_ids_and_locators(self):
        inventory, _ = analyzer.analyze(self.xml)
        self.assertEqual(inventory["objects"][0]["id"], "datasource_0001")
        self.assertEqual(inventory["objects"][0]["locator"], "/workbook/*[1]/*[1]")
        self.assertEqual(len({o["id"] for o in inventory["objects"]}), len(inventory["objects"]))
        self.assertEqual(len({o["locator"] for o in inventory["objects"]}), len(inventory["objects"]))

    def test_dependency_and_dashboard_references(self):
        inventory, _ = analyzer.analyze(self.xml)
        sheet = next(o for o in inventory["objects"] if o["kind"] == "worksheet")
        self.assertTrue(sheet["dependencies"][0]["resolved"])
        self.assertTrue(all(c["resolved"] for c in sheet["dependencies"][0]["columns"]))
        zones = [o for o in inventory["objects"] if o["kind"] == "zone"]
        self.assertEqual(zones[0]["worksheet_ids"], [sheet["id"]])
        self.assertEqual(zones[0]["bounds"]["w"], 100000)
        self.assertFalse(zones[1]["worksheet_reference_resolved"])

    def test_duplicate_names_are_ambiguous_not_silently_resolved(self):
        xml = b'<workbook><datasources><datasource name="x"/><datasource name="x"/></datasources><worksheets><worksheet><datasource-dependencies datasource="x"/></worksheet></worksheets></workbook>'
        inventory, _ = analyzer.analyze(xml)
        sheet = inventory["objects"][-1]
        self.assertFalse(sheet["dependencies"][0]["resolved"])
        self.assertEqual(len(sheet["dependencies"][0]["datasource_ids"]), 2)

    def test_ambiguous_references_are_bounded_and_explicit(self):
        xml = (
            '<workbook><datasources>'
            + '<datasource name="x"><column name="y"/></datasource>' * 40
            + '</datasources><worksheets><worksheet><datasource-dependencies datasource="x">'
            + '<column name="y"/></datasource-dependencies></worksheet></worksheets></workbook>'
        ).encode()
        inventory, _ = analyzer.analyze(xml)
        dependency = inventory["objects"][-1]["dependencies"][0]
        self.assertEqual(len(dependency["datasource_ids"]), 32)
        self.assertEqual(dependency["datasource_candidate_count"], 40)
        self.assertTrue(dependency["datasource_candidates_truncated"])
        self.assertFalse(dependency["resolved"])
        self.assertTrue(dependency["columns"][0]["datasource_unresolved"])
        self.assertIsNone(dependency["columns"][0]["candidate_count"])

    def test_minimal_empty_workbook_is_not_migration_success(self):
        inventory, manifest = analyzer.analyze(b"<workbook/>")
        self.assertEqual(inventory["objects"], [])
        self.assertEqual(manifest["analysis_status"], "inventoried_not_migrated")
        self.assertEqual(manifest["validation"]["desktop_open_refresh"], "not_run")

    def test_packaged_workbook_matches_xml(self):
        data, kind = analyzer.load_workbook(self.package())
        self.assertEqual(data, self.xml)
        inventory, _ = analyzer.analyze(data, kind)
        self.assertEqual(inventory["source_format"], "twbx")

    def test_archive_does_not_extract_or_read_data(self):
        target = self.package([("nested/Workbook.twb", self.xml),
                               ("Data/synthetic.hyper", b"not a real extract")])
        data, _ = analyzer.load_workbook(target)
        self.assertEqual(data, self.xml)
        self.assertFalse((self.work / "Data").exists())

    def test_multiple_workbooks_require_selection(self):
        target = self.package([("one.twb", self.xml), ("two.twb", self.xml)])
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(target)
        self.assertEqual(analyzer.load_workbook(target, "two.twb")[0], self.xml)
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(target, "absent.twb")

    def test_no_workbook_member(self):
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(self.package([("data.txt", b"data")]))

    def test_unsafe_member_paths(self):
        for name in ("../outside", "/absolute", "C:/drive", "a\\b", "a/../b",
                     "a//b", "./b"):
            with self.subTest(name=name), self.assertRaises(analyzer.AnalysisError):
                analyzer.load_workbook(self.package([("safe.twb", self.xml), (name, b"x")]))

    def test_duplicate_and_case_colliding_members(self):
        for second in ("safe.twb", "SAFE.TWB"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                target = self.package([("safe.twb", self.xml), (second, self.xml)])
            with self.assertRaises(analyzer.AnalysisError):
                analyzer.load_workbook(target)

    def test_symlink_rejected(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(self.package([("safe.twb", self.xml), (link, b"target")]))

    def test_encryption_flag_and_unsupported_compression(self):
        info = zipfile.ZipInfo("safe.twb")
        info.flag_bits = 1
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.check_member(info)
        info.flag_bits = 0
        info.compress_type = zipfile.ZIP_BZIP2
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.check_member(info)

    def test_null_truncated_name_rejected(self):
        info = zipfile.ZipInfo("safe.twb\x00evil")
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.check_member(info)

    def test_compression_bomb_rejected(self):
        target = self.package([("safe.twb", b"<workbook>" + b" " * 100000 + b"</workbook>")])
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(target)

    def test_member_count_limit(self):
        target = self.package()
        with patch.object(analyzer, "MAX_MEMBERS", 0), self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(target)

    def test_central_directory_underreported_count_rejected_before_zipfile(self):
        target = self.package([("safe.twb", self.xml), ("other.txt", b"x")])
        data = bytearray(target.read_bytes())
        end = data.rfind(b"PK\x05\x06")
        struct.pack_into("<HH", data, end + 8, 1, 1)
        target.write_bytes(data)
        with patch.object(analyzer.zipfile, "ZipFile") as zip_parser:
            with self.assertRaises(analyzer.AnalysisError):
                analyzer.load_workbook(target)
            zip_parser.assert_not_called()

    def test_zip64_multidisk_and_trailing_data_rejected(self):
        original = self.package().read_bytes()
        end = original.rfind(b"PK\x05\x06")
        cases = []
        zip64 = bytearray(original)
        struct.pack_into("<HH", zip64, end + 8, 65535, 65535)
        cases.append(zip64)
        multidisk = bytearray(original)
        struct.pack_into("<H", multidisk, end + 4, 1)
        cases.append(multidisk)
        cases.append(original + b"unexpected")
        for data in cases:
            with self.subTest(data=data[-22:]), self.assertRaises(analyzer.AnalysisError):
                analyzer.preflight_zip(data)

    def test_corrupt_member_crc_is_safe_cli_failure(self):
        target = self.package(compression=zipfile.ZIP_STORED)
        data = bytearray(target.read_bytes())
        index = data.find(b"<?xml")
        self.assertGreater(index, 0)
        data[index] ^= 1
        target.write_bytes(data)
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(analyzer.main([str(target), "--output-dir", str(self.work / "out")]), 2)
        self.assertIn("invalid ZIP", error.getvalue())
        self.assertFalse((self.work / "out").exists())

    def test_archive_and_member_and_total_limits(self):
        target = self.package()
        for constant in ("MAX_ARCHIVE", "MAX_MEMBER", "MAX_TOTAL", "MAX_XML"):
            with self.subTest(limit=constant), patch.object(analyzer, constant, 1):
                with self.assertRaises(analyzer.AnalysisError):
                    analyzer.load_workbook(target)

    def test_bounded_read(self):
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.bounded_read(io.BytesIO(b"123"), 2)

    def test_twb_load_and_member_rejected(self):
        self.assertEqual(analyzer.load_workbook(FIXTURE), (self.xml, "twb"))
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.load_workbook(FIXTURE, "Workbook.twb")

    def test_nonregular_input_rejected_without_blocking(self):
        # Windows-mounted filesystems need not support creating actual FIFOs.
        with patch.object(analyzer.os, "fstat") as info, \
                patch.object(analyzer.os, "open", wraps=os.open) as low_open:
            info.return_value.st_mode = stat.S_IFIFO
            info.return_value.st_size = 0
            with self.assertRaisesRegex(analyzer.AnalysisError, "regular file"):
                analyzer.load_workbook(FIXTURE)
            if hasattr(os, "O_NONBLOCK"):
                self.assertTrue(low_open.call_args.args[1] & os.O_NONBLOCK)

    def test_dtd_and_entity_rejected(self):
        for xml in (b'<!DOCTYPE workbook [<!ENTITY a "secret">]><workbook>&a;</workbook>',
                    b'<!DOCTYPE workbook SYSTEM "https://example.invalid"><workbook/>',
                    b'<!ENTITY x SYSTEM "file:///etc/passwd"><workbook/>'):
            with self.subTest(xml=xml), self.assertRaises(analyzer.AnalysisError):
                analyzer.analyze(xml)

    def test_encoding_and_namespaces(self):
        for xml in ('<workbook/>'.encode("utf-16"),
                    b'<?xml version="1.0" encoding="iso-8859-1"?><workbook/>',
                    b'<workbook xmlns="urn:test"/>',
                    b'<workbook xmlns:x="urn:test"><x:column/></workbook>'):
            with self.subTest(xml=xml), self.assertRaises(analyzer.AnalysisError):
                analyzer.analyze(xml)
        self.assertEqual(analyzer.analyze(b"\xef\xbb\xbf<workbook/>")[0]["objects"], [])

    def test_malformed_or_wrong_root(self):
        for xml in (b"", b"<workbook>", b"<html/>", b"<workbook>&missing;</workbook>"):
            with self.subTest(xml=xml), self.assertRaises(analyzer.AnalysisError):
                analyzer.analyze(xml)

    def test_xml_structural_limits(self):
        for xml, limit, value in (
            (b"<workbook><a><b/></a></workbook>", "MAX_DEPTH", 2),
            (b"<workbook><a/><b/></workbook>", "MAX_NODES", 2),
            (self.xml, "MAX_XML", 10),
        ):
            with self.subTest(limit=limit), patch.object(analyzer, limit, value):
                with self.assertRaises(analyzer.AnalysisError):
                    analyzer.analyze(xml)

    def test_xml_attribute_length_limit(self):
        xml = b'<workbook secret="' + b"x" * 65537 + b'"/>'
        with self.assertRaises(analyzer.AnalysisError):
                    analyzer.analyze(xml)
        xml = ("<workbook " + " ".join(f'a{i}="x"' for i in range(65)) + "/>").encode()
        with self.assertRaises(analyzer.AnalysisError):
            analyzer.analyze(xml)

    def test_schema_outputs_are_deterministic_and_no_overwrite(self):
        inventory, manifest = analyzer.analyze(self.xml)
        first, second = self.work / "first", self.work / "second"
        analyzer.write_results(first, inventory, manifest)
        analyzer.write_results(second, inventory, manifest)
        for name in ("inventory.json", "compatibility.json"):
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            json.loads((first / name).read_text())
        with self.assertRaises(FileExistsError):
            analyzer.write_results(first, inventory, manifest)

    def test_cli_success_and_refusal_to_overwrite(self):
        out = self.work / "out"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "analyze_tableau.py"),
             str(FIXTURE), "--output-dir", str(out)], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT", result.stdout)
        self.assertTrue((out / "compatibility.json").is_file())
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(analyzer.main([str(FIXTURE), "--output-dir", str(out)]), 2)
        self.assertIn("already exists", error.getvalue())

    def test_cli_safe_errors(self):
        cases = [("secret.twb", b"<workbook SECRET_TOKEN"),
                 ("secret.twbx", b"not zip"),
                 ("secret.txt", b"anything")]
        for name, data in cases:
            path = self.work / name
            path.write_bytes(data)
            with self.subTest(name=name), contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(analyzer.main([str(path), "--output-dir", str(self.work / "out")]), 2)
                self.assertNotIn("SECRET_TOKEN", error.getvalue())
                self.assertNotIn("secret.", error.getvalue())
                self.assertFalse((self.work / "out").exists())

    def test_feature_heuristics(self):
        xml = b'<workbook><datasources><datasource><connection class="hyper"/><connection class="tableau-server"/><relation type="join"/><relation type="union"/><column datatype="spatial"/></datasource></datasources><stories><story/></stories><extension/><relationship/><device-layout/></workbook>'
        inventory, _ = analyzer.analyze(xml)
        for feature in ("extracts", "published_datasources", "joins", "unions",
                        "spatial_fields", "stories", "extensions", "relationships", "device_layouts"):
            self.assertGreater(inventory["features"][feature], 0)

    def test_invalid_bounds_are_not_raw_exported(self):
        xml = b'<workbook><dashboards><dashboard><zones><zone x="SECRET" w="99999999999999999"/></zones></dashboard></dashboards></workbook>'
        inventory, _ = analyzer.analyze(xml)
        zone = inventory["objects"][-1]
        self.assertIsNone(zone["bounds"]["x"])
        self.assertIsNone(zone["bounds"]["w"])
        self.assertNotIn("SECRET", json.dumps(inventory))


if __name__ == "__main__":
    unittest.main()
