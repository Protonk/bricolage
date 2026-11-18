# Build a fixture with two aliases

[The specimen](leaf/README.md) is a 96 × 60 arrow and three variants. Read its
[manifest](leaf/manifest.csv) for the four intended paths, three PNG hashes
and two decoded RGB hashes. The recipe ships as text. It writes the catalog
and media into a new leaf at the path you choose.

## Materialize in a disposable checkout

Start at the Bricolage repository root. With Python 3.14.x installed, run
`make -C Fixtures setup-python` to create the fixture environment if needed.
The materializer uses only the standard library and needs no downloads. The
full check also uses Pillow 12.0.0 from [the fixture requirements](leaf/tools/requirements.txt).

Create a fresh archive under `Fixtures/output/` with the public commands and
the repository's media ignore rules. The Git identity is local to this archive.
Choose a new destination for `leaf` under its `Fixtures/Relationships/` tree.
The commands below use the same shell throughout the exercise.

```sh
origin=$PWD
lab=$(mktemp -d "$origin/Fixtures/output/byte-identities.XXXXXX")
git init -q "$lab"
git -C "$lab" config user.name "Fixture reader"
git -C "$lab" config user.email "fixture@example.invalid"
git -C "$lab" config commit.gpgsign false
cp .gitignore "$lab/"
echo /Fixtures/.venv >> "$lab/.git/info/exclude"
mkdir -p "$lab/Fixtures/Heaps" "$lab/Fixtures/Sampler" "$lab/Fixtures/output"
cp -R Fixtures/tools "$lab/Fixtures/"
cp Fixtures/sample Fixtures/collection "$lab/Fixtures/"
cp Fixtures/Sampler/sampler.py "$lab/Fixtures/Sampler/"
ln -s "$origin/Fixtures/.venv" "$lab/Fixtures/.venv"

leaf="$lab/Fixtures/Relationships/Arrow"
Fixtures/.venv/bin/python Fixtures/Template/Byte-Identities/leaf/tools/materialize.py "$leaf"
cd "$lab"
Fixtures/.venv/bin/python "$leaf/tools/check.py"
Fixtures/collection totals
git add .
git commit -qm 'Materialize the arrow specimen'
```

The validator checks the catalogs, source, batches and probes, hashes the files,
decodes each PNG, and compares B against a horizontal flip of decoded A. Open
`images/01.png` and `images/03.png` in the new leaf to see the two directions.

## Follow one draw through both removals

Stay in the disposable checkout. The original draw records the seed, the
ordered selection and the inventory used to make it. Inspect the saved
inventory's `population.images[].aliases` for the identity shared by 01 and 02.

```sh
Fixtures/sample 3 --seed arrow-aliases > Fixtures/output/draw.json
draw_id=$(Fixtures/.venv/bin/python -c 'import json; print(json.load(open("Fixtures/output/draw.json"))["output"]["world_id"])')
Fixtures/sample keep "$draw_id"
git add Fixtures/Sampler/records
git commit -qm 'Keep original arrow draw'
cat Fixtures/Sampler/records/inventories/*.json
Fixtures/sample show "$draw_id" --paths
```

Initially A's `available_path` ends in `01.png`. Give `collection remove` that
specific path. A hash argument would retire both copies together.

```sh
Fixtures/collection remove "$leaf/images/01.png" --reason 'Retire the first arrow path'
Fixtures/sample inventory
Fixtures/sample publish "$draw_id"
```

The inventory now lists three paths and three eligible identities. Read
`output.published` and `output.receipt_recorded` in the republication response.
Both are true, and A's `available_path` ends in `02.png`. The missing 01 path
and the changed manifest are reported in `problems`, giving exit status 1.

```sh
Fixtures/collection remove "$leaf/images/02.png" --reason 'Retire the remaining arrow path'
Fixtures/sample inventory
Fixtures/sample verify "$draw_id"
Fixtures/sample publish "$draw_id"
cat "Fixtures/output/worlds/$draw_id/world.json"
```

The fresh inventory now lists B and C. `verify` replays the saved inventory
and seed, reporting `original_draw_reproduced: true` and two available images.
The separate `publish` reports `published: false` and an `image-unlisted` problem
naming A. Both commands exit 1. The original world still contains all three
PNGs. Its copies, the retained source and the retired paths under
`previews/removed/` sit outside the active inputs.

[The experiment record](EXPERIMENT.md) compares the independent predictions,
the two placements and the results for this draw.
