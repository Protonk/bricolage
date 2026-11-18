"""Verify the fixture's measurements independently of the generator."""
import hashlib
from pathlib import Path
import sys

from PIL import Image

LEAF = Path(__file__).resolve().parents[1]
FIXTURES = next(p for p in LEAF.parents if (p / "tools/fixture_layout.py").is_file())
sys.path.insert(0, str(FIXTURES / "tools"))
from relationship_fixtures import require, validate


def check():
    rows, _, _ = validate(LEAF)
    decoded = {}
    for row in rows:
        name = row["file"]
        with Image.open(LEAF / name) as im:
            require(im.format == "PNG" and im.mode == "RGB", f"Expected RGB PNG: {name}")
            require(im.size == (row["width"], row["height"]) == (96, 60), f"Unexpected size: {name}")
            pixels = im.tobytes()
            require(hashlib.sha256(pixels).hexdigest() == row["pixels_rgb_sha256"],
                    f"Decoded RGB hash differs: {name}")
            decoded[name] = im.copy()
    a, copy, b, c = [decoded[f"images/{i:02}.png"] for i in range(1, 5)]
    require(len(rows) == 4 and len({r["byte_sha256"] for r in rows}) == 3,
            "Expected four paths and three distinct byte hashes")
    require(a.tobytes() == copy.tobytes() == c.tobytes(), "A, A-copy and C must decode identically")
    require(b.tobytes() != a.tobytes() and b.tobytes() == a.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(),
            "B must be a visibly different horizontal reflection of A")
    print("4 listed paths, 3 byte identities, 2 RGB arrays. B is A reflected horizontally.")


if __name__ == "__main__":
    check()
