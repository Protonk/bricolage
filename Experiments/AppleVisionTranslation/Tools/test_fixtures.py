"""Developer-tool checks; run with python3 -m unittest discover -s Experiments/AppleVisionTranslation/Tools."""
import ast
import csv
from collections import defaultdict
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import fixtures


class FixtureToolTests(unittest.TestCase):
    def testBothSetsUseTheSameSchemaAndMultiviewKeepsIndependentSources(self):
        derivative_rows, _, _ = fixtures.validate(fixtures.CORPUS)
        rows, probes, identity = fixtures.validate(fixtures.MULTIVIEW)
        self.assertEqual(list(derivative_rows[0]), list(rows[0]))
        self.assertEqual(list(fixtures.read_csv(fixtures.CORPUS / "sources.csv")[0]),
                         list(fixtures.read_csv(fixtures.MULTIVIEW / "sources.csv")[0]))
        self.assertEqual((identity["images"], identity["sources"], identity["assets"], identity["scenes"]),
                         (20, 20, 40, 8))
        self.assertEqual(len({row["family_id"] for row in rows}), 20)
        self.assertEqual(sum(p["relation"] == "same_scene" for p in probes), 16)
        self.assertEqual(sum(p["relation"] == "distinct_scene" for p in probes), 25)
        self.assertEqual(sum(p["relation"] == "diagnostic" for p in probes), 3)
        focus = fixtures.select_pairs(rows, probes, "focus", fixtures.MULTIVIEW)
        self.assertEqual(len(focus), 16)
        self.assertEqual(len(fixtures.select_pairs(rows, probes, "full", fixtures.MULTIVIEW)), 44)
        self.assertEqual({p[key] for p in focus for key in ("file_a", "file_b")}, {r["file"] for r in rows})
        self.assertTrue(all(r["pixels_rgb_sha256"] == "" for r in rows))

    def testCommonsDownloadNamesResolveToVerifiedThumbnailSources(self):
        root = fixtures.MULTIVIEW
        archive = root / "provenance/commons"
        proofs = json.loads((archive / "thumbnail-verification.json").read_text())
        mapping = fixtures.read_csv(archive / "import-map.csv")
        rows = {r["file"]: r for r in json.loads((root / "manifest.json").read_text())["images"]}
        sources = {s["family_id"]: s for s in fixtures.read_csv(root / "sources.csv")}
        kit = {r["source_filename"]: r for r in json.loads((archive / "supplied-fixtures.json").read_text())["fixtures"]}
        by_download = {m["downloaded_filename"]: m for m in mapping}
        self.assertEqual(len(proofs), 9)
        self.assertEqual(len(by_download), 9)
        for proof in proofs:
            self.assertEqual(proof["verification"], "exact_sha256")
            imported = by_download[proof["matched_local_file"]]
            self.assertEqual(imported["commons_source_filename"], proof["source_filename"])
            self.assertEqual(imported["byte_sha256"], proof["reference_sha256"])
            image = rows[imported["file"]]
            self.assertEqual(image["byte_sha256"], proof["reference_sha256"])
            self.assertEqual(image["scene_id"], kit[proof["source_filename"]]["scene_group"])
            source = sources[image["family_id"]]
            self.assertEqual(source["source_url"], proof["source_page"])
            self.assertEqual(source["source_filename"], proof["matched_local_file"])
            self.assertIn("thumbnail", source["preprocessing"])
        self.assertEqual(by_download["image-08.jpg"]["commons_source_filename"], "Budapest_pride_20250628_143521_1.jpg")
        self.assertEqual(by_download["image-09.jpg"]["commons_source_filename"], "Budapest_pride_20250628_143521.jpg")

    def testSameSceneIsNotTheSameAsSameSource(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "corpus"
            shutil.copytree(fixtures.MULTIVIEW, root)
            probes = fixtures.read_csv(root / "probes.csv")
            probes[0]["relation"] = "same_bytes"
            with (root / "probes.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(probes[0]))
                writer.writeheader()
                writer.writerows(probes)
            with self.assertRaisesRegex(ValueError, "origin label disagrees"):
                fixtures.validate(root)

    def testCorruptionAndInvalidBatchAreRejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "corpus"
            shutil.copytree(fixtures.CORPUS, root)
            image = next((root / "images").iterdir())
            original = image.read_bytes()
            image.write_bytes(original + b"changed")
            with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                fixtures.validate(root)
            image.write_bytes(original)
            batch = root / "batches/batch-1.txt"
            batch.write_text(batch.read_text() + batch.read_text().splitlines()[0] + "\n")
            with self.assertRaisesRegex(ValueError, "duplicates in batch-1"):
                fixtures.validate(root)

    def testSelectionsCoverIntendedInputs(self):
        rows, probes, _ = fixtures.validate(fixtures.CORPUS)
        focus = fixtures.select_pairs(rows, probes, "focus")
        self.assertEqual(len(focus), 14)
        self.assertEqual(len({p[key] for p in focus for key in ("file_a", "file_b")}), 17)
        self.assertEqual(sum(p["relation"] == "diagnostic" for p in focus), 2)
        full = fixtures.select_pairs(rows, probes, "full")
        self.assertEqual(len(full), 190)
        self.assertEqual({p[key] for p in full for key in ("file_a", "file_b")}, {r["file"] for r in rows})
        self.assertEqual(len({(p["file_a"], p["file_b"]) for p in full}), len(full))

    def testGeneratorRestoresExactSmallBatchListsWithoutRegeneratingImages(self):
        # Execute only the dependency-free batch writer, not main or Pillow's encoders.
        source = fixtures.CORPUS / "tools/generate.py"
        tree = ast.parse(source.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "write_small_batches")
        rows = json.loads((fixtures.CORPUS / "manifest.json").read_text())["images"]
        families = defaultdict(dict)
        for row in rows:
            if row["family_id"]:
                families[row["family_id"]][row["transformation"]] = row
        with tempfile.TemporaryDirectory() as temporary:
            namespace = {"BATCH_DIR": Path(temporary)}
            exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
            namespace["write_small_batches"](families)
            for name in ("smoke.txt", "medium.txt"):
                self.assertEqual((Path(temporary) / name).read_bytes(),
                                 (fixtures.CORPUS / "batches" / name).read_bytes())

    def testRunnerKeepsFailuresVisibleAndContinues(self):
        _, probes, _ = fixtures.validate(fixtures.CORPUS)
        statuses = iter(("failed", "noObservation"))

        def invoke(arguments, **kwargs):
            if arguments == ["swift", "--version"]:
                return subprocess.CompletedProcess(arguments, 0, "test toolchain", "")
            destination = Path(arguments[-1])
            destination.mkdir()
            status = next(statuses)
            (destination / "comparison.json").write_text(json.dumps({
                "alignment": {"status": status, "explanation": "Test unavailable alignment"}}))
            return subprocess.CompletedProcess(arguments, 2, status, "diagnostic")

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            with patch.object(fixtures, "select_pairs", return_value=probes[:2]), \
                    patch.object(fixtures.subprocess, "run", side_effect=invoke), \
                    patch.object(fixtures.platform, "platform", return_value="test platform"), \
                    redirect_stdout(io.StringIO()):
                code = fixtures.run(fixtures.CORPUS, Path(__file__), output, "focus")
            summary = json.loads((output / "run.json").read_text())
            self.assertEqual(code, 1)
            self.assertTrue(summary["complete"])
            self.assertTrue(summary["fixtures_unchanged"])
            self.assertEqual(summary["counts"], {"failed": 1, "noObservation": 1})
            self.assertEqual(summary["results"][0]["stderr"], "diagnostic")
            with self.assertRaisesRegex(ValueError, "Output already exists"):
                fixtures.run(fixtures.CORPUS, Path(__file__), output, "focus")


if __name__ == "__main__":
    unittest.main()
