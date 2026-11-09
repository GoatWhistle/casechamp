import json
import os
import pathlib

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[2]
FONTS = pathlib.Path(os.environ["ONEST_DIR"])
OUT = ROOT / "frontend" / "src" / "shared" / "ui" / "brand" / "iso-text" / "iso-glyphs.json"
WORK = ROOT / "work" / "brand"

SIZE = 76.0
WEIGHT = 700
TRACK = -2.0
RINGS = 3
STEP = 6.5
LINE = 2.2
GAP = 11.0
PAD = 1.5
WORDS = {
    "notFound": ("404", "onest-latin-wght-normal.woff2"),
    "failure": ("сбой", "onest-cyrillic-wght-normal.woff2"),
}


class FlatPen(BasePen):
    def __init__(self, glyph_set, steps=10):
        super().__init__(glyph_set)
        self.contours = []
        self.current = []
        self.steps = steps

    def _moveTo(self, p):
        self.current = [p]

    def _lineTo(self, p):
        self.current.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.current[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.current.append(
                (
                    mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
                    mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1],
                )
            )

    def _qCurveToOne(self, p1, p2):
        p0 = self.current[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.current.append(
                (
                    mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0],
                    mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1],
                )
            )

    def _closePath(self):
        if len(self.current) > 2:
            self.contours.append(self.current)
        self.current = []

    _endPath = _closePath


def load_font(name):
    font = TTFont(FONTS / name)
    instantiateVariableFont(font, {"wght": WEIGHT}, inplace=True)
    path = WORK / f"iso-{name}.ttf"
    font.flavor = None
    font.save(path)
    return font, path


def letters_of(font, path, text):
    blob = hb.Blob.from_file_path(str(path))
    shaper = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(shaper, buf, {"kern": True, "liga": False})
    scale = SIZE / font["head"].unitsPerEm
    track = TRACK / scale
    glyph_set = font.getGlyphSet()
    order = font.getGlyphOrder()
    x = 0.0
    letters = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = FlatPen(glyph_set)
        glyph_set[order[info.codepoint]].draw(pen)
        geom = Polygon()
        for contour in pen.contours:
            pts = [((px + x + pos.x_offset) * scale, -(py + pos.y_offset) * scale) for px, py in contour]
            geom = geom.symmetric_difference(Polygon(pts).buffer(0))
        letters.append(geom)
        x += pos.x_advance + track
    return letters


def fill_holes(geom):
    parts = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    return unary_union([Polygon(p.exterior) for p in parts if not p.is_empty])


def to_path(geom):
    parts = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for poly in parts:
        if poly.is_empty:
            continue
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)[:-1]
            out.append("M" + "L".join(f"{cx:.2f} {cy:.2f}" for cx, cy in coords) + "Z")
    return "".join(out)


def rings(solid):
    out = []
    for k in range(RINGS):
        d = GAP + STEP * k
        outer = solid.buffer(d + LINE / 2, quad_segs=24, join_style="round")
        inner = solid.buffer(d - LINE / 2, quad_segs=24, join_style="round")
        out.append(outer.difference(inner).simplify(0.03))
    return out


def glyph(text, font_name):
    font, path = load_font(font_name)
    letters = letters_of(font, path, text)
    path.unlink()
    word = unary_union(letters)
    solid = unary_union([fill_holes(g) for g in letters])
    word_rings = rings(solid)
    minx, miny, maxx, maxy = unary_union([word, *word_rings]).bounds
    view_box = f"{minx - PAD:.2f} {miny - PAD:.2f} {maxx - minx + 2 * PAD:.2f} {maxy - miny + 2 * PAD:.2f}"
    return {"viewBox": view_box, "word": to_path(word.simplify(0.02)), "rings": [to_path(g) for g in word_rings]}


def main():
    data = {key: glyph(text, font) for key, (text, font) in WORDS.items()}
    OUT.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf8")
    print({key: value["viewBox"] for key, value in data.items()}, OUT.stat().st_size)


main()
