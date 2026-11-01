# The world hazy receives

hazy receives a **world**: an independently produced directory containing image
files and a manifest. It does not read the producer's records or source tree. This document is the
whole of what hazy may assume about a world, and the whole of what it owes back.

## Layout

```text
WORLD/
  world.json
  3d4741a1c8d645e90a80e5b73dd662ac89b37c6b636924de7092f3e0d0a54609.jpg
  5337794668a689da1ae70912eec2fbf1f0414692cc7a5c5a40a94fb3ffd74a12.png
  …
```

```json
{
  "schema_version": 1,
  "world_id": "draw-82acd83c6cd540a6bf4e29610ff5dc2d",
  "images": [
    {"id": "sha256:3d4741a1c8d6…a54609", "file": "3d4741a1c8d6…a54609.jpg"},
    {"id": "sha256:5337794668a6…d74a12", "file": "5337794668a6…d74a12.png"}
  ]
}
```

## What hazy may rely on

- Every file's SHA-256 equals its stem. A world verifies itself without the manifest.
- No two files share bytes. The list is sorted by file name and carries no order.
- `world.json` is written last, inside the staged directory. If it is present, the
  world is complete. The directory contains the manifest and the files, nothing else.
- The world ID is the opaque ID of a saved draw. Republishing that draw preserves
  its world ID. Repeating a draw with the same size, seed and population reproduces
  the image selection but creates a new draw and world ID.
- Fields are only added within a schema version, never removed or retyped. Readers
  ignore fields they do not know. A later per-image public attribute would appear as
  an optional key on the image object.

## What hazy owes

- Refer to images by their ID, never by path. Name the world ID in anything emitted
  about the world.
- Treat the directory as read-only and expect no other files in it. Any stray entry,
  such as a `.DS_Store` written by browsing the world in Finder, makes the world
  invalid until its producer republishes it.
- Finish consuming a world before its publisher reuses that directory, or use a
  separate publication directory. Atomic replacement switches whole directories;
  it does not pin one version across a reader's separate file opens.
- Handle an undecodable file as an ordinary error. The sampler verifies bytes, not
  that an image decodes.

## What hazy must not expect

Order, groups, pairs, roles, truth, or metadata beyond the bytes themselves. The
world says which images exist and nothing about why. Any structure hazy finds
came from the images.

## The other side

Mapping a world ID and its image IDs back to where the images came from is an
activity of the world's producer. The producer keeps the records that make that possible and decides,
case by case, whether anything hazy produced from a world is worth keeping.

This contract is shared by [hazy](../hazy/WORLD.md) and
[bricolage](../bricolage/WORLD.md). Keep both copies identical when changing it.
