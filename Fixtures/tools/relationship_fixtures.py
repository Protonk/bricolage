#!/usr/bin/env python3
"""Check a provenance relationship set or run local comparisons. Standard library only."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "Fixtures/Relationships/Derivatives"
MULTIVIEW = REPO / "Fixtures/Relationships/Multiviews"
sys.path.insert(0, str(REPO / 'Fixtures/Sampler'))
import sampler


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def asset(root, name):
    parts = PurePosixPath(name).parts
    require(len(parts) == 2 and parts[0] in ("images", "sources")
            and parts[1] not in (".", ".."), f"Invalid asset path: {name}")
    path = root / name
    require(path.resolve().parent == (root / parts[0]).resolve()
            and not path.is_symlink(), f"Asset must be a local file: {name}")
    return path


def validate_pairs(pairs, by_file):
    seen = set()
    for probe in pairs:
        key = (probe["file_a"], probe["file_b"])
        require(key not in seen, f"Duplicate probe: {key}")
        seen.add(key)
        require(all(name in by_file for name in key), f"Unknown probe image: {key}")
        left, right = (by_file[name] for name in key)
        relation = probe["relation"]
        require(bool(probe["interpretation"]), f"Missing probe interpretation: {key}")
        if relation == "distinct_origin":
            require(left["family_id"] != right["family_id"], f"Probe origin label disagrees: {key}")
        elif relation == "same_scene":
            require(left["scene_id"] and left["scene_id"] == right["scene_id"]
                    and left["family_id"] != right["family_id"], f"Probe scene label disagrees: {key}")
        elif relation == "distinct_scene":
            require(left["scene_id"] and right["scene_id"] and left["scene_id"] != right["scene_id"],
                    f"Probe scene label disagrees: {key}")
        elif relation != "diagnostic":
            require(relation in ("same_bytes", "same_decoded_pixels", right["transformation"])
                    or relation.startswith("same_origin_"), f"Unknown probe relation: {relation}")
            require(left["family_id"] and left["family_id"] == right["family_id"],
                    f"Probe origin label disagrees: {key}")
        if relation in ("same_bytes", "same_decoded_pixels"):
            field = "byte_sha256" if relation == "same_bytes" else "pixels_rgb_sha256"
            require(left[field] and left[field] == right[field], f"Probe identity labels disagree: {key}")



# Active catalogs are checked separately from the preserved publication.
from pathlib import Path as _RemovalPath
import sys as _removal_sys
_removal_tools = next(p / 'tools' for p in _RemovalPath(__file__).resolve().parents if (p / 'tools/fixture_layout.py').is_file())
_removal_sys.path.insert(0, str(_removal_tools))
from fixture_removal import publication_check

@publication_check
def validate(root):
    manifest = json.loads((root / "manifest.json").read_text())
    require(manifest["schema_version"] == 1 and manifest["kind"] in ("derivatives", "multiview"),
            "Unsupported fixture schema or kind")
    rows = manifest["images"]
    require(bool(rows), "Empty fixture manifest")
    require([{k: str(v) for k, v in r.items()} for r in rows]
            == read_csv(root / "manifest.csv"), "CSV and JSON manifests disagree")
    by_file = {r["file"]: r for r in rows}
    require(len(by_file) == len(rows), "Duplicate manifest paths")
    actual = {f"images/{p.name}" for p in (root / "images").iterdir() if p.name != ".DS_Store"}
    require(set(by_file) == actual, "Manifest does not cover images/ exactly")

    checksums = {}
    for line in (root / "SHA256SUMS.txt").read_text().splitlines():
        expected, name = line.split("  ", 1)
        require(name not in checksums, f"Duplicate checksum path: {name}")
        require(digest(asset(root, name)) == expected, f"Checksum mismatch: {name}")
        checksums[name] = expected
    source_files = {f"sources/{p.name}" for p in (root / "sources").iterdir() if p.name != ".DS_Store"}
    require(set(checksums) == actual | source_files, "Checksums must cover all images and sources")
    sources = read_csv(root / "sources.csv")
    require(len(sources) > 0 and len({s["family_id"] for s in sources}) == len(sources),
            "Source families must be distinct")
    require({"sources/" + s["source_filename"] for s in sources} == source_files,
            "Source credits do not cover sources/ exactly")
    source_hashes = {}
    source_by_family = {}
    for source in sources:
        require(source["source_sha256"] == checksums["sources/" + source["source_filename"]],
                f"Source checksum disagrees: {source['family_id']}")
        source_hashes[source["family_id"]] = source["source_sha256"]
        source_by_family[source["family_id"]] = source
    for row in rows:
        require(row["byte_sha256"] == checksums[row["file"]],
                f"Manifest checksum disagrees: {row['file']}")
        require(row["width"] > 0 and row["height"] > 0, f"Invalid dimensions: {row['file']}")
        require(1 <= row["exif_orientation"] <= 8, f"Invalid orientation: {row['file']}")
        parents = row["parents"].split("|")
        require(len(parents) == row["origin_count"] and set(parents) <= source_hashes.keys(),
                f"Invalid parents: {row['file']}")
        require((row["family_id"] == parents[0] and len(parents) == 1)
                or (row["family_id"] == "" and len(parents) == 2),
                f"Family disagrees with parents: {row['file']}")
        if row["transformation"] in ("source", "singleton", "byte_copy"):
            require(row["byte_sha256"] == source_hashes[row["family_id"]],
                    f"Source/copy bytes disagree: {row['file']}")
            source = source_by_family[row["family_id"]]
            require(all(row[field] == int(source[field]) for field in ("width", "height", "exif_orientation")),
                    f"Source dimensions/orientation disagree: {row['file']}")
        if row["scene_id"]:
            require(len(parents) == 1 and source_by_family[parents[0]]["scene_id"] == row["scene_id"],
                    f"Scene disagrees with source: {row['file']}")
        if manifest["kind"] == "multiview":
            require(row["scene_id"] and row["relation_kind"] == "independent_capture"
                    and row["transformation"] == "source", f"Invalid multiview capture: {row['file']}")

    partition = []
    batch_names = sorted({r["batch"] for r in rows})
    require(all(name.startswith("batch-") and name[6:].isdigit() for name in batch_names), "Invalid batch name")
    for name in (*batch_names, "smoke", "medium"):
        paths = (root / "batches" / f"{name}.txt").read_text().splitlines()
        require(len(paths) == len(set(paths)) and set(paths) <= by_file.keys(),
                f"Invalid paths or duplicates in {name}")
        if name.startswith("batch-"):
            require(all(by_file[p]["batch"] == name for p in paths), f"Assignments disagree: {name}")
            partition.extend(paths)
        elif manifest["kind"] == "derivatives":
            variants = {"source", "byte_copy"}
            if name == "medium":
                variants.update(("reencode_png", "jpeg_q94", "center_crop_85"))
            require(set(paths) == {r["file"] for r in rows if r["transformation"] in variants},
                    f"Selection disagrees: {name}")
    require(len(partition) == len(rows) and set(partition) == by_file.keys(),
            "Batches must partition all images exactly once")

    probes = read_csv(root / "probes.csv")
    validate_pairs(probes, by_file)
    selection = json.loads((root / "selections.json").read_text())
    require(bool(selection["pairs"]), "Empty focused selection")
    validate_pairs(selection["pairs"], by_file)
    require(set(selection["known_shift_families"]) <= source_hashes.keys(), "Unknown known-shift family")
    # Pixel hashes above are checked for label consistency, not recomputed with Pillow.
    return rows, probes, {
        "fixture_id": manifest["fixture_id"], "schema_version": manifest["schema_version"],
        "kind": manifest["kind"], "images": len(rows), "assets": len(checksums), "sources": len(sources),
        "scenes": len({r["scene_id"] for r in rows if r["scene_id"]}), "probes": len(probes),
        "metadata_sha256": {str(p.relative_to(root)): digest(p) for p in [
            root / "manifest.json", root / "manifest.csv", root / "sources.csv",
            root / "SHA256SUMS.txt", root / "probes.csv", root / "selections.json",
            *sorted((root / "batches").glob("*.txt")),
        ]},
    }


def select_pairs(rows, probes, selection, root=CORPUS):
    families = defaultdict(dict)
    for row in rows:
        if row["family_id"]:
            families[row["family_id"]][row["transformation"]] = row["file"]

    def pair(left, right, relation, note):
        return dict(file_a=left, file_b=right, relation=relation, interpretation=note)

    if selection == "focus":
        return json.loads((root / "selections.json").read_text())["pairs"]
    pairs = list(probes)
    if selection == "full":
        seen = {(p["file_a"], p["file_b"]) for p in pairs}
        for row in rows:
            family = row["family_id"]
            if not family:
                references = [families[parent]["source"] for parent in row["parents"].split("|")]
            elif row["transformation"] == "singleton":
                references = [row["file"]]  # Input coverage, not evidence of retrieval quality.
            elif row["transformation"] == "source":
                continue
            else:
                references = [families[family]["source"]]
            for reference in references:
                key = (reference, row["file"])
                if key not in seen:
                    pairs.append(pair(*key, row["transformation"], "provenance_only_no_expected_alignment"))
                    seen.add(key)
    return pairs


def load_world(world, store):
    """Validate the supplied world and join its ID to a saved draw on this side only."""
    require(not (world / 'world.json').is_symlink(), 'World manifest must be a regular local file')
    manifest = sampler.read_json(world / 'world.json', 'World manifest')
    require(isinstance(manifest, dict), 'World manifest must be an object')
    require(type(manifest.get('schema_version')) is int and manifest['schema_version'] == 1,
            'Unsupported world schema')
    draw, _ = sampler.load_draw(store, manifest.get('world_id'))
    entries = manifest.get('images')
    require(isinstance(entries, list), 'World images must be a list')
    images, files = {}, set()
    for entry in entries:
        require(isinstance(entry, dict), 'World image entry must be an object')
        image_id, name = entry.get('id'), entry.get('file')
        require(isinstance(image_id, str) and image_id in draw['image_ids'], 'World has an image outside its saved draw')
        require(isinstance(name, str) and '/' not in name and '\\' not in name and '\0' not in name
                and Path(name).stem == image_id.removeprefix('sha256:'), 'Unsafe or non-hash world filename')
        require(image_id not in images and name not in files, 'Duplicate world image ID or file')
        path = world / name
        require(path.is_file() and not path.is_symlink(), 'World image must be a regular local file: ' + image_id)
        require('sha256:' + digest(path) == image_id, 'World image checksum differs: ' + image_id)
        images[image_id] = name
        files.add(name)
    require(set(images) == set(draw['image_ids']), 'World image membership differs from its saved draw')
    require(list(images.values()) == sorted(files), 'World images must be sorted by filename')
    present, expected = {p.name for p in world.iterdir()}, files | {'world.json'}
    require(present == expected, 'World file coverage differs; unexpected entries: '
            + (', '.join(sorted(present - expected)) or 'none') + '; missing entries: '
            + (', '.join(sorted(expected - present)) or 'none'))
    return manifest['world_id'], images


def run(root, binary, output, selection, world, store=None):
    store = sampler.resolve_store(REPO) if store is None else store
    rows, probes, identity = validate(root)
    pairs = select_pairs(rows, probes, selection, root)
    require(binary.is_file(), f"Comparison executable not found: {binary}")
    require(not sampler.within(output, root), "Output must be outside the fixture corpus")
    require(not sampler.within(output, world), "Output must be outside the world")
    require(not output.exists(), f"Output already exists: {output}")
    world_id, world_images = load_world(world, store)
    # Record the Swift toolchain when one is on PATH. Only the executable is required.
    try:
        swift = subprocess.run(["swift", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        swift = None
    output.mkdir()  # The parent must already exist, as for the consumer's own output.
    (output / "pairs").mkdir()
    summary = dict(
        corpus=identity, selection=selection, world_id=world_id, started_utc=datetime.now(timezone.utc).isoformat(),
        system=platform.platform(), swift=swift, binary_sha256=digest(binary),
        runner_sha256=digest(Path(__file__)),
        interpretation="Outcomes describe alignment, not matching accuracy; notRun is not a failed request.",
        complete=False, results=[],
    )
    by_file = {r["file"]: r for r in rows}

    def save():
        (output / "run.json").write_text(json.dumps(summary, indent=2) + "\n")

    save()
    for index, probe in enumerate(pairs, 1):
        destination = output / "pairs" / f"{index:03d}"
        result = dict(probe, output=str(destination.relative_to(output)),
                      reference=by_file[probe["file_a"]], floating=by_file[probe["file_b"]])
        reference_id = 'sha256:' + result['reference']['byte_sha256']
        floating_id = 'sha256:' + result['floating']['byte_sha256']
        missing = sorted({reference_id, floating_id} - world_images.keys())
        if missing:
            result.update(status='skipped', output=None, reason='probe endpoints absent from the supplied world',
                          missing_image_ids=missing)
            summary['results'].append(result)
            save()
            print(f"{index}/{len(pairs)} {probe['relation']}: skipped (endpoints absent)", flush=True)
            continue
        try:
            process = subprocess.run([str(binary), 'compare', '--world', str(world),
                                      '--reference', reference_id, '--floating', floating_id, '--output', str(destination)],
                                     capture_output=True, text=True, timeout=60)
            result.update(exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr)
            report = destination / "comparison.json"
            result["status"] = "error"
            if report.exists():
                result["report"] = json.loads(report.read_text())
                require(result['report'].get('worldID') == world_id
                        and result['report']['reference']['id'] == reference_id
                        and result['report']['floating']['id'] == floating_id, 'Report world/image identities disagree')
                status = result["report"]["alignment"]["status"]
                expected_exit = 0 if status == "estimated" else 2
                require(status in ("estimated", "notRun", "failed", "noObservation")
                        and process.returncode == expected_exit, "Report and process exit disagree")
                result["status"] = status
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            result.update(status="error", error=str(error))
        summary["results"].append(result)
        save()  # Keep completed outcomes visible if a later comparison is interrupted.
        print(f"{index}/{len(pairs)} {probe['relation']}: {result['status']}", flush=True)
    try:
        _, _, after = validate(root)
        require(after == identity, "Fixture metadata changed during the run")
        summary["fixtures_unchanged"] = True
    except (OSError, ValueError, KeyError) as error:
        summary.update(fixtures_unchanged=False, integrity_error=str(error))
    summary["counts"] = dict(Counter(r["status"] for r in summary["results"]))
    summary["complete"] = True
    save()
    print(json.dumps(summary["counts"], sort_keys=True))
    print(f"Reports and overlays: {output}")
    return 1 if not summary["fixtures_unchanged"] or any(
        r["status"] in ("error", "failed") for r in summary["results"]) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "run"))
    parser.add_argument("--fixtures", type=Path, default=CORPUS)
    parser.add_argument("--selection", choices=("focus", "probes", "full"), default="focus")
    parser.add_argument("--binary", type=Path, help="Explicit path to the hazy-vision-translation executable (required for run)")
    parser.add_argument("--output", type=Path)
    parser.add_argument('--world', type=Path, help='Sampler-published world (required for run)')
    parser.add_argument('--store', type=Path, help='Saved draw record store; default the sampler\'s scratch store')
    args = parser.parse_args()
    try:
        if args.command == "check":
            _, _, identity = validate(args.fixtures.resolve())
            print(json.dumps(identity, indent=2))
            return 0
        require(args.output is not None, "run requires --output NEW_DIRECTORY")
        require(args.binary is not None, "run requires --binary PATH_TO_HAZY_VISION_TRANSLATION")
        require(args.world is not None, 'run requires --world WORLD_DIRECTORY')
        return run(args.fixtures.resolve(), args.binary.resolve(), args.output.resolve(), args.selection,
                   args.world.resolve(), args.store.resolve() if args.store else None)
    except (OSError, ValueError, KeyError, sampler.SamplerError, subprocess.SubprocessError) as error:
        print(f"fixtures: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
