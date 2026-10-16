import json
from pathlib import Path
import unittest


STARTER = Path(__file__).resolve().parents[1] / "templates" / "starter"


class StarterTests(unittest.TestCase):
    def test_project_and_model_references_exist(self):
        project = json.loads((STARTER / "Starter.pbip").read_text())
        report = STARTER / project["artifacts"][0]["report"]["path"]
        definition = json.loads((report / "definition.pbir").read_text())
        model = report / definition["datasetReference"]["byPath"]["path"]
        self.assertTrue((model / "definition.pbism").is_file())
        self.assertTrue((model / "definition" / "database.tmdl").is_file())
        self.assertTrue((model / "definition" / "model.tmdl").is_file())
        self.assertIn("partition Synthetic = m",
                      (model / "definition" / "tables" / "Synthetic.tmdl").read_text())

    def test_page_order_and_names_resolve(self):
        pages = STARTER / "Starter.Report" / "definition" / "pages"
        metadata = json.loads((pages / "pages.json").read_text())
        self.assertIn(metadata["activePageName"], metadata["pageOrder"])
        for name in metadata["pageOrder"]:
            page = json.loads((pages / name / "page.json").read_text())
            self.assertEqual(page["name"], name)
            self.assertIn("STARTER ONLY", page["displayName"])
            self.assertGreater(page["height"], 0)
            self.assertGreater(page["width"], 0)

    def test_all_json_files_have_public_schema_identifiers(self):
        files = list(STARTER.rglob("*.json")) + list(STARTER.rglob("*.pbip"))
        files += list(STARTER.rglob("*.pbir")) + list(STARTER.rglob("*.pbism"))
        self.assertEqual(len(files), 7)
        for file in files:
            content = json.loads(file.read_text())
            self.assertTrue(content["$schema"].startswith("https://developer.microsoft.com/json-schemas/"))
        # This is a local structural test, not JSON Schema or Desktop validation.


if __name__ == "__main__":
    unittest.main()
