#!/usr/bin/env python3
"""Build the local, image-led heap tour. No network or fixture mutations."""

import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


HEAPS = Path(__file__).resolve().parents[1]
ROOT = HEAPS.parents[1]
W, H, M = 648, 792, 36
PAPER, INK = '#F4F1EA', '#202522'
MUTED, ACCENT = '#677068', '#9B4435'


def plain(value):
    text = re.sub(r'<(style|script)\b.*?</\1>', '', str(value or ''), flags=re.S)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    text = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def load_collections(plan):
    """Resolve only manifest inputs and verify the frozen publication selection."""
    collections = []
    manifests = {
        str(p.parent.relative_to(HEAPS)) for p in HEAPS.rglob('manifest.json')
        if not {'provenance', 'previews', 'sources', 'images'}.intersection(p.parts)
    }
    assert manifests == {c['leaf'] for c in plan['collections']}, 'Collection roster changed'
    for number, chapter in enumerate(plan['collections'], 1):
        leaf = HEAPS / chapter['leaf']
        rows = json.loads((leaf / 'manifest.json').read_text())['images']
        assert len(rows) == chapter['count'], f'Count changed: {leaf}'
        indices = [round(i * (len(rows) - 1) / 11) for i in range(12)]
        assert [i + 1 for i in indices] == chapter['indices']
        assert [rows[i]['file'] for i in indices] == chapter['files']
        assert 1 <= chapter['hero'] <= 12
        imports = {r['final_file']: r for r in json.loads(
            (leaf / 'provenance/import-map.json').read_text())}
        with (leaf / 'sources.csv').open(newline='') as f:
            sources = {r['family_id']: r for r in csv.DictReader(f)}
        # The summary counts describe present acquired inputs, not pending leads.
        assert all((leaf / r['file']).is_file() for r in rows)
        pictures = []
        for sample, index in enumerate(indices, 1):
            row = rows[index]
            path = leaf / row['file']
            assert path.resolve().parent == (leaf / 'images').resolve()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row['byte_sha256']
            with Image.open(path) as im:
                im.load()
                assert im.size == (row['width'], row['height'])
                assert im.format == row['format']
                assert getattr(im, 'n_frames', 1) == 1, 'Animated inputs need a display decision'
            source = sources[row['family_id']]
            record = imports[row['file']]
            title = (record.get('canonical_title') or record.get('commons_title')
                     or source['subject'])
            url = record.get('source_url') or record.get('file_page') or source['source_url']
            assert url.startswith('https://commons.wikimedia.org/')
            assert record.get('license'), f'Missing license: {path}'
            pictures.append(dict(path=path, record=record, title=plain(title), url=url,
                                 ref=f'{number:02d}.{sample:02d}'))
        collections.append(dict(chapter, pictures=pictures, number=number))
    assert sum(c['count'] for c in collections) == plan['counts']['images']
    assert len(collections) == plan['counts']['collections']
    assert len({c['leaf'].split('/')[0] for c in collections}) == plan['counts']['heaps']
    return collections


def artist_credit(chapter, record):
    if chapter['leaf'].endswith('Botanical-Illustrations'):
        parts = ['Artist: ' + plain(record.get('original_artist') or 'unknown')]
        for field, label in [('engraver_lithographer', 'Engraver'), ('digitizer', 'Digitizer')]:
            if record.get(field):
                parts.append(label + ': ' + plain(record[field]))
    elif chapter['leaf'].endswith('US-Army-SSI'):
        parts = ['Original creator: ' + plain(record.get('original_creator') or 'unknown')]
        for field, label in [('designer', 'Designer'), ('digital_renderer', 'Renderer')]:
            if record.get(field):
                parts.append(label + ': ' + plain(record[field]))
    elif chapter['leaf'].endswith('Evan-Amos-Uploads'):
        parts = [plain(record.get('original_creator') or 'Creator unknown')]
        if record.get('digital_modifier'):
            parts.append('Digital modifier: ' + plain(record['digital_modifier']))
    else:
        parts = [plain(record.get('attribution_credit') or record.get('creator')
                       or 'Creator unknown')]
    return '; '.join(parts).replace('Unknown authorUnknown author', 'Creator unknown')


class Book:
    def __init__(self, output, plan, collections):
        self.c = canvas.Canvas(str(output), pagesize=(W, H), pageCompression=1, invariant=1)
        self.c.setTitle('hazy / heaps - A visual tour')
        self.c.setAuthor('hazy')
        self.c.setSubject('A picture book of the Similarity and Curatorial heaps')
        self.plan, self.collections = plan, collections
        self.pages = 0
        self.used = set()

    def start(self, label='', dark=False, bookmark=None):
        self.pages += 1
        self.dark = dark
        self.bg, self.fg = (INK, PAPER) if dark else (PAPER, INK)
        self.c.setFillColor(HexColor(self.bg))
        self.c.rect(0, 0, W, H, fill=1, stroke=0)
        if bookmark:
            self.c.bookmarkPage(bookmark)
        if label:
            self.text(label.upper(), M, H - 37, 8.5, 'Sans', self.fg, tracking=1.5)

    def text(self, value, x, y, size=10, font='Sans', color=None, tracking=0):
        self.c.saveState()
        t = self.c.beginText(x, y)
        t.setFont(font, size)
        t.setFillColor(HexColor(color or self.fg))
        t.setCharSpace(tracking)
        t.textOut(value)
        self.c.drawText(t)
        self.c.restoreState()

    def para(self, value, x, top, width, size=12, font='Serif', leading=None, color=None):
        style = ParagraphStyle('book', fontName=font, fontSize=size,
                               leading=leading or size * 1.3, textColor=HexColor(color or self.fg))
        p = Paragraph(value, style)
        _, height = p.wrap(width, H)
        assert top - height >= 35, f'Text below page: {value[:100]}'
        p.drawOn(self.c, x, top - height)
        return height

    def picture(self, picture, x, y, width, height):
        self.used.add(picture['ref'])
        with Image.open(picture['path']) as original:
            im = ImageOps.exif_transpose(original)
            ratio = min(width / im.width, height / im.height)
            iw, ih = im.width * ratio, im.height * ratio
            px, py = x + (width - iw) / 2, y + (height - ih) / 2
            # Make display copies in memory at up to 180 dpi. Never crop or
            # write the source/input files. Small originals are not upsampled.
            im.thumbnail((math.ceil(iw * 2.5), math.ceil(ih * 2.5)), Image.Resampling.LANCZOS)
            if original.format == 'JPEG':
                display = io.BytesIO()
                im.convert('RGB').save(display, format='JPEG', quality=90, optimize=True)
                display.seek(0)
                reader = ImageReader(display)
            else:
                reader = ImageReader(im.convert('RGBA'))
            self.c.drawImage(reader, px, py, iw, ih, mask='auto')
        self.c.linkURL(picture['url'], (px, py, px + iw, py + ih), relative=0, thickness=0)

    def finish(self, label='hazy / heaps'):
        color = '#B8BDB6' if self.dark else MUTED
        self.text(label, M, 25, 8, color=color)
        self.text(f'{self.pages:02d}', W - M - 12, 25, 8, color=color)
        self.c.showPage()

    def cover(self):
        self.start('hazy / a picture book', bookmark='cover')
        self.text('heaps', M - 4, 640, 104, 'Serif')
        self.text('A visual tour', M, 605, 21, 'SerifItalic')
        picks = [(0, 0), (2, 6), (6, 0), (7, 8), (10, 4), (5, 8)]
        for n, (chapter, sample) in enumerate(picks):
            pic = self.collections[chapter]['pictures'][sample]
            x, y = M + n % 3 * 198, 341 - n // 3 * 205
            self.picture(pic, x, y, 180, 187)
            self.text(pic['ref'], x, y - 12, 7, color=MUTED)
        self.text('Similarity / Curatorial', M, 83, 12, 'Sans')
        self.text(self.plan['edition'], M, 62, 9, color=MUTED)
        self.finish('')

    def contents(self):
        self.start('A way through', bookmark='contents')
        self.c.addOutlineEntry('A way through', 'contents')
        self.para('A collection of<br/>ways to look.', M, 710, 560, 38, 'Serif', 43)
        self.para('A flash of red. A quiet sky. A tangle of branches. Then a turn toward '
                  'wings, buildings, gestures and things made to be held. These pages '
                  'wander through the images already gathered in hazy\'s heaps.',
                  M, 590, 505, 14, 'Serif', 20)
        self.text('868 images / 12 collections / 2 heaps', M, 488, 15, 'Sans')
        self.para('A selection from the acquired images. Each collection gets a large plate '
                  'and a contact sheet. Picture numbers lead to the credits; images link '
                  'to their source pages.', M, 463, 500, 10, 'Sans', 15, MUTED)
        for group, x in [(0, M), (1, 336)]:
            self.text('SIMILARITY' if group == 0 else 'CURATORIAL', x, 362, 9, tracking=1.5)
            for j, chapter in enumerate(self.collections[group * 6:group * 6 + 6]):
                page = 4 + j * 2 if group == 0 else 18 + j * 2
                y = 325 - j * 38
                self.para(html.escape(chapter['title']), x, y + 11, 227, 11, 'Serif', 13)
                self.text(str(page), x + 252, y, 9, 'Sans')
                self.c.linkRect('', f'chapter-{chapter["number"]}',
                                (x, y - 15, x + 270, y + 14), thickness=0)
        self.para('The heaps keep two different collecting habits: visual prompts in '
                  'Similarity, published source collections in Curatorial.',
                  M, 74, 560, 10, 'SerifItalic', 14, MUTED)
        self.finish()

    def opener(self, group):
        dark = group == 'Similarity'
        self.start('I / Similarity' if dark else 'II / Curatorial', dark, group)
        self.c.addOutlineEntry(group, group)
        self.text(group, M, 661, 53, 'Serif')
        note = ('Color, spacing, light, repetition, growth, texture.\n'
                'Six invitations to notice the surface of a picture.' if dark else
                'A contest gallery, an emblem, a botanical page, an object portrait.\n'
                'The source collection sets the frame.')
        self.para(html.escape(note).replace('\n', '<br/>'), M, 615, 565, 15, 'Serif', 21)
        picks = [(0, 3), (3, 0), (4, 8)] if dark else [(6, 6), (9, 3), (11, 11)]
        for n, (i, j) in enumerate(picks):
            pic = self.collections[i]['pictures'][j]
            self.picture(pic, M + n * 198, 196, 180, 300)
            self.text(pic['ref'], M + n * 198, 176, 8)
        self.finish()

    def chapter(self, chapter):
        n = chapter['number']
        pic = chapter['pictures'][chapter['hero'] - 1]
        dark = n in (1, 5, 7)
        self.start(f'{n:02d} / {chapter["label"]}', dark, f'chapter-{n}')
        self.c.addOutlineEntry(chapter['title'], f'chapter-{n}', level=1)
        if chapter['layout'] == 'portrait':
            title_size = 28 if n == 8 else 34
            self.para(html.escape(chapter['title']), M, 688, 205, title_size, 'Serif', title_size + 4)
            self.para(html.escape(chapter['caption']), M, 505, 180, 15, 'SerifItalic', 21)
            self.picture(pic, 264, 105, 348, 591)
        else:
            self.para(html.escape(chapter['title']), M, 706, 575, 36, 'Serif', 41)
            self.para(html.escape(chapter['caption']), M, 603, 540, 15, 'SerifItalic', 21)
            self.picture(pic, M, 115, 576, 439)
        self.text(f'Plate {pic["ref"]}', M, 69, 8)
        self.finish()

        self.start(f'{n:02d} / {chapter["label"]}')
        self.text('A closer look', M, 705, 25, 'Serif')
        self.text('Twelve pictures from the collection', M, 681, 9, color=MUTED)
        for i, pic in enumerate(chapter['pictures']):
            x, y = M + i % 3 * 198, 512 - i // 3 * 146
            self.picture(pic, x, y, 180, 124)
            self.text(pic['ref'], x, y - 13, 7.5, color=MUTED)
        self.finish(chapter['title'])

    def interlude(self):
        self.start('An interval', dark=True)
        pic = self.collections[2]['pictures'][5]
        self.picture(pic, M, 210, 576, 440)
        self.text('Let the eye rest.', M, 133, 24, 'SerifItalic')
        self.text(pic['ref'], M, 92, 8)
        self.finish()

    def closing(self):
        self.start('One more look')
        self.text('Back to the pictures.', M, 684, 35, 'Serif')
        for n, (i, j) in enumerate([(4, 7), (10, 7), (3, 3), (11, 4)]):
            pic = self.collections[i]['pictures'][j]
            x, y = M + n % 2 * 294, 374 - n // 2 * 255
            self.picture(pic, x, y, 282, 226)
            self.text(pic['ref'], x, y - 13, 8, color=MUTED)
        self.para('The tour ends here. The collections stay open.', M, 65, 570, 12, 'SerifItalic')
        self.finish()

    def credits(self):
        for spread in range(6):
            self.start('Picture credits', bookmark='credits' if spread == 0 else None)
            if spread == 0:
                self.c.addOutlineEntry('Picture credits', 'credits')
            self.para('Picture titles link to Commons; license names link to terms where supplied. '
                      'Credits follow the stored source records. Full framing is retained; '
                      'display copies are resized and compressed for this PDF. '
                      'Numbers identify pictures throughout the book.',
                      M, 719, 576, 9, 'Sans', 12, MUTED)
            for col, chapter in enumerate(self.collections[spread * 2:spread * 2 + 2]):
                x, width = M + col * 300, 276
                self.para(f'{chapter["number"]:02d} / ' + html.escape(chapter['title']),
                          x, 648, width, 16, 'Serif', 19)
                entries = []
                for pic in chapter['pictures']:
                    r = pic['record']
                    title = re.sub(r'^File:', '', pic['title'])
                    title = re.sub(r'\.(jpe?g|png|gif|svg|tiff?)$', '', title, flags=re.I)
                    license_text = html.escape(plain(r['license']))
                    if r.get('license_url'):
                        license_text = f'<a href="{html.escape(r["license_url"], quote=True)}">{license_text}</a>'
                    text = (f'<b>{pic["ref"]}</b> '
                            f'<a href="{html.escape(pic["url"], quote=True)}">{html.escape(title)}</a>'
                            f'<br/>{html.escape(artist_credit(chapter, r))}. {license_text}.')
                    credit = plain(r.get('credit'))
                    # Preserve explicit credit notices for CC works; archival
                    # source URLs remain accessible through each source-page link.
                    if r['license'].startswith('CC BY') and credit and credit != 'Own work':
                        if not credit.startswith('https://'):
                            text += ' ' + html.escape(credit)
                    if r.get('restrictions'):
                        text += ' Recorded restriction: ' + html.escape(plain(r['restrictions'])) + '.'
                    entries.append(text)
                for size in (8.5, 8, 7.5):
                    style = ParagraphStyle('credit', fontName='Unicode', fontSize=size,
                                           leading=size * 1.28, textColor=HexColor(INK))
                    paras = [Paragraph(t, style) for t in entries]
                    heights = [p.wrap(width, H)[1] for p in paras]
                    if sum(heights) + 7 * 11 <= 544:
                        break
                else:
                    raise ValueError(f'Credits overflow for {chapter["leaf"]}')
                y = 597
                for p, height in zip(paras, heights):
                    p.drawOn(self.c, x, y - height)
                    y -= height + 7
                assert y >= 42
            self.finish()

    def build(self):
        self.cover()
        self.contents()
        self.opener('Similarity')
        for chapter in self.collections[:6]:
            self.chapter(chapter)
        self.interlude()
        self.opener('Curatorial')
        for chapter in self.collections[6:]:
            self.chapter(chapter)
        self.closing()
        self.credits()
        assert self.pages == 36
        assert self.used == {p['ref'] for c in self.collections for p in c['pictures']}
        self.c.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/pdf/hazy-heaps-tour.pdf')
    parser.add_argument('--font-dir', type=Path, default=Path('/System/Library/Fonts/Supplemental'))
    args = parser.parse_args()
    for name, filename in [('Serif', 'Georgia.ttf'), ('SerifItalic', 'Georgia Italic.ttf'),
                           ('Sans', 'Arial.ttf'), ('Unicode', 'Arial Unicode.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(args.font_dir / filename)))
    pdfmetrics.registerFontFamily('Unicode', normal='Unicode', bold='Unicode', italic='Unicode')
    plan = json.loads((HEAPS / 'tour-guide.json').read_text())
    collections = load_collections(plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    book = Book(args.output, plan, collections)
    book.build()
    print(f'{args.output}: {book.pages} pages, {len(book.used)} sampled images; '
          f'{plan["counts"]["images"]} acquired images across {len(collections)} collections')


if __name__ == '__main__':
    main()
