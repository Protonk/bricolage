# Lift Fixtures into bricolage

This is the execution handoff for making Fixtures the main application in
`~/Desktop/Experiments/bricolage`, currently empty. The preparation repairs are
complete in hazy; the lift itself has not started. Read [WORLD.md](WORLD.md),
[Fixtures/AGENTS.md](Fixtures/AGENTS.md) and the [sampler guide](Fixtures/Sampler/README.md).

## Decisions and boundaries

- bricolage owns the fixture collections, intake tools, sampler, durable records,
  and optional probe-pair runner. Keep `Fixtures/` as a top-level directory so
  recorded paths and metadata pins remain valid. The root README and guidance
  present these as bricolage's application, with `Fixtures/sample` as its entry point.
- hazy consumes a world and receives no fixture provenance. The world ID is a saved
  draw's ID. Repeating a draw reproduces the selection, not the ID; republishing
  the saved draw preserves the ID. `Fixtures/sample show SAMPLE_ID` resolves the
  provenance on the bricolage side, on demand.
- World installation and publication receipts are separate operations. A successful
  command installs the world and appends one `publication` annotation. Receipt or
  cleanup failure returns a named problem and exit 1 while accurately reporting
  whether the world was installed. Follow the sampler guide's recovery instructions;
  do not mistake a nonzero exit for proof that no publication happened.
- Keep the existing probe runner, as requested. Its fixture validation is independent
  of hazy, and comparisons require an explicit binary path. Adapt its invocation to
  the world CLI in task 1; provenance and probe selection stay on the Fixtures side.
  There is no scorer, evaluation loop or automatic consumer-result retention.
- Preserve original image bytes, metadata pins, draw records and annotation history.
  Images remain Git-ignored. No acquisition, regeneration, ID rewrite or reroll is
  part of the lift. Existing acquisition shortfalls remain documented as they are.
- Preserve the original Git commit IDs by making a full local clone and pruning
  unrelated files at the new tip. Historical hazy files remain in bricolage's history;
  physical separation is sufficient. Do not use subtree split or history filtering:
  the former strips the required prefix, and both rewrite provenance commit IDs.
  There is no shared object store or continuing remote dependency after the clone.
- Do not push. Flattening hazy's history is outside this plan and requires a separate
  explicit request. No subsequent research pathway is selected here.

## Preparation completed in hazy

- Shared relationship validation, its tests and the optional runner are now
  `Fixtures/tools/relationship_fixtures.py` and `test_relationships.py`. All three leaf
  entry points and Variants' builder use them. The runner requires `--binary`.
- Publication exchanges whole directories atomically; unsupported replacement fails
  without deleting the previous world. Cleanup and receipt failures stay visible.
- An unavailable redundant alias remains a reported problem but does not prevent
  publishing an available verified copy of the selected identity.
- Malformed leaf fields, unreadable metadata and non-UTF-8 annotations are reported
  through the JSON error/problem interface. `list` includes draw directories whose
  `draw.json` is missing. Regression tests cover these failure paths.
- `WORLD.md` now distinguishes repeatable selections from stable saved-draw IDs and
  documents the reader's need to finish before the publication directory is reused.

Recheck this preparation before task 1:

```sh
make -C Fixtures test-sampler
make -C Fixtures test-fixture-layout
make -C Fixtures test-relationships
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
Fixtures/sample verify draw-82acd83c6cd540a6bf4e29610ff5dc2d
```

The supplied media currently passes all 18 leaf validators and the demonstration
has all 12 selected images available. New missing media or failed checks must be
resolved, not waived as an expected consequence of moving repositories.

Preparation was checked on macOS with Python 3.14.9: 47 sampler tests, 8 layout
tests and 8 relationship-tool tests passed. A temporary standalone checkout with
no Experiments directory passed all 18 leaf validators (25 specialized checks),
verified and republished the demonstration, and retained identical copies of all
5,971 asset files and 213 asset directories. The original durable records were
unchanged. The Linux directory-exchange path has not been exercised here.

## 1. Implement and prove hazy's world boundary

Completed in hazy on 2026-11-01 while Fixtures remains available. The isolated
consumer built and passed all 14 Swift tests with HAZY_WORLD set (no skips), emitted
only world/image identities, rejected unknown IDs and altered bytes, and preserved
its inputs. The runner executed 14 focus probes against a full-population world
(all estimated) and explicitly skipped 14 absent-endpoint probes against the
demonstration. The independent Fixtures checkout passed 47 sampler, 8 layout and
10 runner/relationship tests plus all 18 leaf validators. Temporary record stores
kept the original demonstration history unchanged. Tasks 2 and 3 remain pending.

- Give the experiment's pair CLI this explicit interface:
  `hazy-vision-translation compare --world WORLD --reference IMAGE_ID --floating IMAGE_ID --output DIRECTORY`.
  Read `world.json`, validate its supported schema, unique IDs/files, safe flat
  paths, file coverage and byte hashes, and resolve the two supplied IDs. Ignore
  unknown additive fields. Never infer pairs or expected results from fixture
  structure. The internal comparison implementation may still use file URLs.
- Reports and readable summaries identify the world and both image IDs rather than
  source paths. Include those identities in world-related errors when available.
  Keep world inputs read-only and require outputs outside the world. Preserve the
  existing distinction between estimated, unavailable, notRun and failed outcomes.
  Treat undecodable bytes as an ordinary input error, not a bad sampling decision.
- Replace `FixtureTests.swift`'s manifest, family, scene and known-shift assumptions
  with world-based checks selected by `HAZY_WORLD`. Do not bake the demonstration's
  IDs, image counts or successful decode/alignment assumptions into general world
  tests. Retain the seven self-contained mechanics cases and add focused world
  parsing, identity, output and failure checks. Provenance assertions belong to
  Fixtures; remove them from hazy without inventing a new evaluation system.
- Adapt `Fixtures/tools/relationship_fixtures.py run` and its tests to require `--world` as
  well as `--binary`. Resolve that world's saved draw using the local sampler store,
  map the explicit fixture probes to byte IDs, and pass only the world and those IDs
  to hazy. Report probe endpoints absent from the world as skipped with a reason;
  never replace them or assemble an unrecorded world. Exact-byte aliases may map a
  probe to a self-comparison. Keep `check` independent of any world or binary.
- Update the experiment README and IMAGE-JOURNEY for the implemented interface and
  actual checks. Remove active fixture-path instructions from hazy's experiment
  docs. Keep current fixture-side commands in Fixtures' docs. Update the portability
  ledger if any framework handoff or caller-visible convention changes.

Acceptance requires a real consumer exercise, not just rewritten tests:

1. Publish the saved demonstration to a new disposable world via `Fixtures/sample
   publish`, using a temporary copy of the record store for this proof so the durable
   demonstration's annotation history is unchanged.
2. Copy the updated tracked hazy application sources into a temporary checkout with
   **no Fixtures directory**. With `HAZY_WORLD` pointing at the world outside that
   checkout, `swift build` and `swift test` pass. Missing `HAZY_WORLD` must not prevent
   the self-contained mechanics tests from running; the acceptance run must show
   that the real-world checks actually ran, not merely skipped.
3. Invoke the built CLI on two IDs from the supplied world, with a fresh output
   directory outside it. An estimated or unavailable alignment is acceptable;
   verify the report has the exact world/image IDs, no origin paths or provenance,
   and that the world bytes are unchanged. Also exercise an unknown image ID and
   an altered copy of a world; both fail visibly without writing into the world.
4. Run the adapted runner against a sampler-published world containing its probe
   endpoints and an explicit binary in the temporary hazy checkout. A full-population
   draw through `Fixtures/sample N` may be used for coverage; keep its store/output
   temporary. Check executed and missing-endpoint outcomes without treating an
   alignment estimate as a match judgment.
5. Independently check a temporary Fixtures-only checkout, with media, Python
   dependencies, WORLD.md and standalone root AGENTS.md, but no `Experiments/`,
   using every preparation command above. Three source-tool pin checks use the
   root AGENTS.md as their checkout-location marker; they do not read hazy guidance.

Commit task 1 and its docs after these checks. Keep media-ignore rules and the
fixture directory in hazy throughout this task.

## 2. Establish and verify bricolage

Start from task 1's clean, committed hazy revision. Capture the branch and full
commit ID for the lift record. Confirm the destination remains empty; preserve
any unexpected contents instead of overwriting them.

From hazy's root, use task-specific shell variables:

```sh
lift_source=$(pwd -P)
lift_destination="$HOME/Desktop/Experiments/bricolage"
lift_branch=$(git branch --show-current)
lift_commit=$(git rev-parse HEAD)
git clone --no-hardlinks --single-branch --branch "$lift_branch" "$lift_source" "$lift_destination"
git -C "$lift_destination" remote remove origin
```

This retains every ancestor of the source branch with its original ID and avoids
Git alternates/hard links. Record `lift_commit` in a new textual provenance receipt
under `Fixtures/provenance/`; do not change historical pins or commit references.
Verify representative historical references with `git cat-file -e COMMIT^{commit}`,
including `fd04a3ed21a6cb706a486418997dc6e4ba1e7ff2` and
`6f789b0c36246aaa697dbee800e9c1e6c82d56f0`.

In bricolage only:

- Remove the tracked `Experiments/`, `Research/`, root `output/`, `VERSION` and
  `FIXTURE-LIFT-PLAN.md` from the new tip. Keep Fixtures, WORLD.md and the media-ignore
  rules. Replace the root README and AGENTS with standalone bricolage guidance,
  including setup, sampling, records, fixture validation, the optional runner and
  local commit/no-push rules. Remove obsolete root Swift/output ignore exceptions;
  retain `.venv`, cache and whole-directory media/output ignores needed by Fixtures.
- Copy the ignored media before touching hazy's copy. For example, with the captured
  variables still set, copy the fixture tree while excluding only its disposable
  top-level environment/output and Python caches:

  ```sh
  rsync -a --checksum --exclude='/.venv/' --exclude='/output/' --exclude='__pycache__/' "$lift_source/Fixtures/" "$lift_destination/Fixtures/"
  ```

  Inventory every file beneath each leaf's `images/`, `sources/` and `previews/`,
  including nested files and empty directories. Compare relative paths, sizes and
  SHA-256 hashes before and after. Record counts and inventory digests in the lift
  receipt. The clone's existing tracked records must remain byte-identical except
  for explicitly reviewed documentation changes and the new receipt.
- Create a fresh environment; do not transfer or reuse hazy's venv:

  ```sh
  make -C Fixtures setup-python
  Fixtures/.venv/bin/python -m pip install -r Fixtures/tools/requirements.txt
  ```

  Python 3.14.x and Pillow 12.0.0 cover the current offline validators. Optional
  tools keep their separate requirements. Do not acquire any fixture images.
- Keep WORLD.md identical in both repositories. Add the same counterpart note to
  both copies, linking `../hazy/WORLD.md` and `../bricolage/WORLD.md`. Keep the contract
  pointer in hazy's root guidance after the fixture-specific guidance is removed.
- Run all five preparation commands in bricolage. Publish the saved demonstration
  through bricolage's launcher to a new disposable world and require exit 0,
  `published: true`, `receipt_recorded: true`, verified hashes and the original world
  ID. This real publication appends a new durable receipt; keep it and update the
  demonstration's current annotation-count documentation. Exercise inventory and
  show to check that live paths resolve into bricolage and snapshot pins still match.
- Check that all media is still ignored, no binary assets are staged, the repository
  has no remote, and its Git object store has no alternates. Commit the standalone
  bricolage application and its lift receipt after verification.

Keep hazy's Fixtures and ignore rules intact until bricolage has passed all gates.
A failed transfer, pin check or validator stops the cutover.

## 3. Cut over hazy

Only after the verified bricolage commit exists:

- Move hazy's remaining local Fixtures directory to a named backup outside both
  checkouts; keep it for rollback. Stage the tracked Fixtures deletion. Do not leave
  the ignored media behind in hazy after removing its ignore rules.
- In the **same commit**, remove hazy's fixture media/output ignore rules and Python
  toolchain instructions. Move the root README's fixture-specific introduction to
  bricolage's README as needed, replace its project-map row with a bricolage pointer,
  and keep WORLD.md prominently linked. Remove the completed lift-plan file and its
  links from hazy's README/AGENTS; record the completed boundary in current guidance.
- Build/test hazy with Fixtures absent, run the real CLI against a world published by
  bricolage, verify world/image IDs and input preservation, and rerun bricolage's
  fixture checks. Check the two WORLD.md files are byte-identical. No live command or
  implementation in either repository may depend on the other repository's source
  tree. Explicit binary/world arguments and cross-repository documentation pointers
  are the intended connections. Historical provenance paths remain historical.
- Commit hazy's cutover. Report both commit IDs, checks, the backup location and any
  existing acquisition shortfalls. Leave both repositories unpushed.

These three tasks are separate checked stopping points. Do not perform the
cutover merely because a clone exists or the mechanics tests pass.
