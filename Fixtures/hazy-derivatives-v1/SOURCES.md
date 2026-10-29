# Sources and rights notes

The `sources/` files are byte-for-byte copies of the **scikit-image 0.26.0** bundled sample images, not photographs retrieved from a user's collection. Scikit-image documents their origins and copyright status in the [official image-data API reference](https://scikit-image.org/docs/stable/api/skimage.data.html). Each asset's checksum is in `sources.csv` and `SHA256SUMS.txt`.

| Source file | Description / upstream credit | Status reported by scikit-image |
|---|---|---|
| `astronaut.png` | Eileen Collins astronaut photo, NASA | Public domain / no known restrictions |
| `chelsea.png` | Chelsea the cat, Stefan van der Walt | CC0 |
| `coffee.png` | Coffee cup, Rachel Michetti | CC0 |
| `rocket.jpg` | DSCOVR Falcon 9 launch photo, SpaceX | Public domain |
| `hubble_deep_field.jpg` | Hubble eXtreme Deep Field, NASA | Public domain |
| `camera.png` | Grayscale photographer, Lav Varshney | CC0 (replacement for a previously restricted image) |
| `brick.png` | Brick texture, CC0Textures | CC0 |
| `grass.png` | Grass texture, DeviantArt source | CC0 |
| `gravel.png` | Gravel texture, CC0Textures | CC0 |
| `retina.jpg` | Retina photograph, Wikimedia Commons | CC0 |
| `horse.png` | Horse silhouette, Andreas Preuss | CC0 |
| `coins.png` | Greek coins, Brooklyn Museum | No known copyright restrictions (not labeled CC0) |
| `clock_motion.png` | Motion-blurred clock, Stefan van der Walt | Public domain |
| `cell.png` | Quantitative phase image of cell in saline | CC0 |
| `microaneurysms.png` | Retinal image crop, Andreas Maier | CC0 |

Some originals are grayscale scientific photographs, textures, or an illustration. They are included deliberately: a natural-photo-only corpus would not test how a general image input set behaves across different visual material.

**Important distinction:** A public-domain status or CC0 dedication in source documentation refers to the *image*. This document does not purport to license scikit-image's library code or to make a general claim about other assets distributed by that library.
