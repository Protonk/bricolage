# Multiview sources and rights notes

## Motorcycle pair

The provenance below is retained from the supplied motorcycle fixture. The two
fixture images were supplied by the user. The complete supplied description is
in [provenance/supplied-README.md](provenance/supplied-README.md).

The two RGB PNGs were supplied as byte-for-byte copies of scikit-image 0.26.0's
`motorcycle_left.png` and `motorcycle_right.png`. They originate in the Middlebury
2014 stereo Motorcycle scene. They are separate physical captures, geometrically
rectified upstream and downsampled by a factor of four by scikit-image. Neither
view was made by transforming the other.

The supplied credit names Nera Nesic, Porter Westling, Xi Wang, York Kitajima,
Greg Krathwohl, and Daniel Scharstein at Middlebury College. It records Middlebury's
permission to use and publish the images and disparity maps, with citation
requested. This is not a CC0 designation.

- [Middlebury 2014 stereo scenes](https://vision.middlebury.edu/stereo/data/scenes2014/)
- [Middlebury permission and citation guidance](https://vision.middlebury.edu/stereo/data/)
- [scikit-image stereo_motorcycle documentation](https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.stereo_motorcycle)

Requested research citation, as supplied: D. Scharstein, H. Hirschmüller,
Y. Kitajima, G. Krathwohl, N. Nesic, X. Wang, and P. Westling, “High-resolution
stereo datasets with subpixel-accurate ground truth,” GCPR 2014, Münster, Germany.

## Personal photographs

The user supplied nine photographs for this hazy fixture on 2026-10-29:
`IMG_7067.JPG`, `IMG_7068.JPG`, `IMG_7069.JPG`, `IMG_7242.JPG`, `IMG_7243.JPG`,
`IMG_7246.JPG`, `IMG_7678.JPG`, `IMG_7679.JPG`, and `IMG_7680.JPG`.

They were moved unchanged from `hazy-personal-v1/` to `sources/`, and copied
byte-for-byte into `images/` with opaque filenames. The source catalog and import
map retain original names and SHA-256 hashes. No previous editing or export history
was supplied; `source` means the file as received. These personal images have no
supplied public redistribution license and do not inherit Middlebury's terms.

## Commons crowd sequences

The user manually downloaded these nine JPEGs when Commons access blocks prevented
the kit's intended full-resolution downloads. They were supplied on 2026-10-29 in
`hazy-quasi-multiview-v1/images/` as `image-01.jpg` through `image-09.jpg`, moved
unchanged into `sources/`, and copied byte-for-byte into `images/` under opaque names.

Each download was matched by exact SHA-256 to a named Commons thumbnail. The Kumbh
pair is 1280×851; the four landscape Budapest files are 1280×720; the three portrait
Budapest files are 960×1706. These are upstream reduced-resolution JPEGs. No claim
is made that their hashes match the full-resolution Commons originals. The mapping,
reference URLs and verification evidence are preserved in
[provenance/commons/](provenance/commons/README.md).

The supplied kit credits **Michael T Balonek** for the Kumbh pair under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), and **Vauia Rex**
for the Budapest images under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
Individual source pages are linked below; author and license entries are retained
from the kit in `sources.csv`. The attribution and upstream resizing history stay
with the images. No additional image changes were made during ingestion.

| Downloaded filename | Commons source page | Supplied credit / license |
|---|---|---|
| `image-01.jpg` | [2019_Feb_04_-_Kumbh_Mela_-_Mauni_Amavasya_Crowd_15.jpg](https://commons.wikimedia.org/wiki/File:2019_Feb_04_-_Kumbh_Mela_-_Mauni_Amavasya_Crowd_15.jpg) | Michael T Balonek / CC BY-SA 4.0 |
| `image-02.jpg` | [2019_Feb_04_-_Kumbh_Mela_-_Mauni_Amavasya_Crowd_17.jpg](https://commons.wikimedia.org/wiki/File:2019_Feb_04_-_Kumbh_Mela_-_Mauni_Amavasya_Crowd_17.jpg) | Michael T Balonek / CC BY-SA 4.0 |
| `image-03.jpg` | [Budapest_pride_20250628_142359.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_142359.jpg) | Vauia Rex / CC0 1.0 |
| `image-04.jpg` | [Budapest_pride_20250628_142401.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_142401.jpg) | Vauia Rex / CC0 1.0 |
| `image-05.jpg` | [Budapest_pride_20250628_142817.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_142817.jpg) | Vauia Rex / CC0 1.0 |
| `image-06.jpg` | [Budapest_pride_20250628_142820.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_142820.jpg) | Vauia Rex / CC0 1.0 |
| `image-07.jpg` | [Budapest_pride_20250628_143517.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_143517.jpg) | Vauia Rex / CC0 1.0 |
| `image-08.jpg` | [Budapest_pride_20250628_143521_1.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_143521_1.jpg) | Vauia Rex / CC0 1.0 |
| `image-09.jpg` | [Budapest_pride_20250628_143521.jpg](https://commons.wikimedia.org/wiki/File:Budapest_pride_20250628_143521.jpg) | Vauia Rex / CC0 1.0 |

The original kit's README and metadata remain byte-identical under
`provenance/commons/supplied-*`. Their references to full-resolution originals and
planned local names describe the intended assembly, not the files received. The
canonical manifest, source catalog, and import mapping record the actual inputs.
