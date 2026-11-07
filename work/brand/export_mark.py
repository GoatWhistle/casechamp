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
FONT = pathlib.Path(os.environ["ONEST_DIR"]) / "onest-latin-wght-normal.woff2"
OUT_DOCS = ROOT / "docs" / "brand"
OUT_WORK = ROOT / "work" / "brand"

SIZE = 76.0
WEIGHT = 700
TRACK = -2.0
RINGS = 3
STEP = 6.5
LINE = 2.2
GAP = 11.0
LIGHT = {"ink": "#0e1012", "stops": ("#0066db", "#b9d5f8")}
DARK = {"ink": "#ffffff", "stops": ("#5aa6ff", "#1d4f8f")}


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
            self.current.append((mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0], mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1]))

    def _closePath(self):
        if len(self.current) > 2:
            self.contours.append(self.current)
        self.current = []

    _endPath = _closePath


def load_font():
    font = TTFont(FONT)
    instantiateVariableFont(font, {"wght": WEIGHT}, inplace=True)
    path = OUT_WORK / "onest-700.ttf"
    font.flavor = None
    font.save(path)
    return font, path


def shape(path, text):
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": False})
    return buf.glyph_infos, buf.glyph_positions


def glyph_geometry(font, path, text):
    upm = font["head"].unitsPerEm
    scale = SIZE / upm
    track = TRACK / scale
    glyph_set = font.getGlyphSet()
    order = font.getGlyphOrder()
    infos, positions = shape(path, text)
    x = 0.0
    letters = []
    for info, pos in zip(infos, positions):
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


def mix(a, b, t):
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def rings(solid, count, gap, step, line):
    out = []
    for k in range(count):
        d = gap + step * k
        outer = solid.buffer(d + line / 2, quad_segs=24, join_style="round")
        inner = solid.buffer(d - line / 2, quad_segs=24, join_style="round")
        out.append(outer.difference(inner).simplify(0.03))
    return out


def svg(word_geom, ring_geoms, palette, pad=1.5, cls=False):
    minx, miny, maxx, maxy = unary_union([word_geom, *ring_geoms]).bounds
    vb = f"{minx - pad:.2f} {miny - pad:.2f} {maxx - minx + 2 * pad:.2f} {maxy - miny + 2 * pad:.2f}"
    n = len(ring_geoms)
    body = []
    for k, geom in enumerate(ring_geoms):
        color = mix(*palette["stops"], k / (n - 1) if n > 1 else 0)
        attr = f'class="mark-accent mark-ring-{k + 1}"' if cls else f'fill="{color}"'
        body.append(f'<path {attr} fill-rule="evenodd" d="{to_path(geom)}"/>')
    attr = 'class="mark-base"' if cls else f'fill="{palette["ink"]}"'
    body.append(f'<path {attr} fill-rule="evenodd" d="{to_path(word_geom.simplify(0.02))}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{"".join(body)}</svg>\n', vb


def main():
    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    font, path = load_font()
    letters = glyph_geometry(font, path, "plexus")
    word = unary_union(letters)
    solid = unary_union([fill_holes(g) for g in letters])
    word_rings = rings(solid, RINGS, GAP, STEP, LINE)
    light, vb = svg(word, word_rings, LIGHT)
    dark, _ = svg(word, word_rings, DARK)
    (OUT_DOCS / "wordmark-light.svg").write_text(light, encoding="utf8")
    (OUT_DOCS / "wordmark-dark.svg").write_text(dark, encoding="utf8")

    x_letter = glyph_geometry(font, path, "x")[0]
    x_solid = fill_holes(x_letter)
    x_rings = rings(x_solid, 1, 7.0, 6.0, 4.4)
    symbol, svb = svg(x_letter, x_rings, LIGHT, pad=1.0, cls=True)
    (OUT_DOCS / "symbol.svg").write_text(symbol, encoding="utf8")

    x_rings3 = rings(x_solid, RINGS, GAP, STEP, LINE)
    data = {
        "wordmark": {"viewBox": vb, "word": to_path(word.simplify(0.02)), "rings": [to_path(g) for g in word_rings]},
        "symbol": {"viewBox": svb, "word": to_path(x_letter.simplify(0.02)), "rings": [to_path(g) for g in x_rings]},
        "symbolFull": {
            "viewBox": svg(x_letter, x_rings3, LIGHT, pad=1.0)[1],
            "word": to_path(x_letter.simplify(0.02)),
            "rings": [to_path(g) for g in x_rings3],
        },
        "params": {"size": SIZE, "weight": WEIGHT, "track": TRACK, "rings": RINGS, "step": STEP, "line": LINE, "gap": GAP},
        "light": LIGHT,
        "dark": DARK,
    }
    (OUT_WORK / "mark-paths.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    (OUT_WORK / "onest-700.ttf").unlink()
    print("wordmark", vb, "symbol", svb, "bytes", len(light), len(symbol))


main()
