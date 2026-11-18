# bricolage fixtures

This directory contains the image collections, their records, and the tools for
checking and sampling them. A **leaf** is a collection directory with its own
`manifest.json`; the directories above it group related collections.

## Collections

| Location | What it contains |
|---|---|
| [Relationships](Relationships/README.md) | Derivatives of known sources, separate captures of scenes, and constructed or generated variants |
| [Heaps / Similarity](Heaps/Similarity/README.md) | Collections chosen by visual prompts: red accents in green surroundings, speckled fields, pale skies, repeated rectangles, tangled growth, spreading patches, and puddle reflections |
| [Heaps / Curatorial](Heaps/Curatorial/README.md) | Selections from published collections: Commons POTY categories, insignia, botanical illustrations, Evan Amos uploads, rocks, hand axes and bookplates |

The relationship sets record how images are connected. The heaps record why
images were selected. Both can inform a test, but neither supplies the result an
image matcher should return.

The [heap guide](Heaps/README.md) also describes the local picture book of
selected images and how to rebuild it.

The [collection totals](COLLECTIONS.md) and the [source index](INDEX.csv) are
generated from active manifests: the current input count and distinct byte
hashes for every leaf, and one row per input with its source identity.
Acquisition is incomplete in Speckled-Fields (11 accepted images pending) and
Botanical Illustrations (one transfer pending). POTY Arthropods acquired 43 inputs
against a target of 50. Some Curatorial selections also have earlier unresolved
review cases; their later selections remain provisional. Each collection's README
and records give the details.

## Working with the archive

Use the [root quick start](../README.md) to draw a world. For a new collection,
start with the [fixture template](Template/README.md), [format](FORMAT.md) and
[sourcing handoff](WEB-AGENT-GUIDE.md). Each leaf has a README describing its
selection evidence and checks. The [collection tools](tools/README.md) cover
removal, re-pinning and validation. [RECOVERY.md](RECOVERY.md) describes how
to recover local media from its recorded sources.
