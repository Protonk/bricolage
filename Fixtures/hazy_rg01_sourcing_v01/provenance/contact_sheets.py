#!/usr/bin/env python3
"""Render cached previews without cropping or network access."""
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1]
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
records=[json.loads(p.read_text()) for p in sorted((ROOT/'provenance/downloads').glob('*-320.json'))]
out=ROOT/'previews/contact-sheets'; out.mkdir(parents=True,exist_ok=True)
for offset in range(0,len(records),20):
    page=records[offset:offset+20]; canvas=Image.new('RGB',(1280,math.ceil(len(page)/4)*290),'#eeeeee'); draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(page):
        with Image.open(ROOT/r['file']) as im:
            im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((310,245))
            x=(i%4)*320; y=(i//4)*290; canvas.paste(im,(x+(320-im.width)//2,y+(250-im.height)//2))
            draw.text((x+10,y+255),r['candidate_id'],font=font,fill='black')
    canvas.save(out/f'{offset//20+1:02d}.jpg',quality=90)
print(len(records),'previews')
