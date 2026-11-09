import base64
import json
import pathlib

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parents[2]
SRC = HERE / "src"
FONTS = ROOT / "frontend/node_modules/@fontsource-variable/onest/files"

VARIANTS = [
    ("1-izohrony", "v1"),
    ("2-spletenie", "v2"),
    ("3-marshrut", "v3"),
    ("4-tablo", "v4"),
]


def font(name):
    return base64.b64encode((FONTS / name).read_bytes()).decode("ascii")


def read(name):
    return (SRC / name).read_text(encoding="utf8")


def main():
    mark = json.loads(read("mark.json"))
    data = {
        "symbol": mark["symbol"],
        "icons": json.loads(read("icons.json")),
    }
    css = (
        read("base.css")
        .replace("{{FONT_LATIN}}", font("onest-latin-wght-normal.woff2"))
        .replace("{{FONT_CYR}}", font("onest-cyrillic-wght-normal.woff2"))
    )
    base_js = read("base.js")
    for slug, key in VARIANTS:
        if not (SRC / f"{key}.html").exists():
            continue
        page = read(f"{key}.html")
        extra = dict(data)
        if "{{WORDMARK}}" in page:
            extra["wordmark"] = json.loads(read("wordmark.json"))
        if "{{ATLAS}}" in page:
            extra["atlas"] = json.loads(read("atlas.json"))
        payload = "const DATA = " + json.dumps(extra, ensure_ascii=False, separators=(",", ":")) + ";\n"
        page = (
            page.replace("{{BASE_CSS}}", css)
            .replace("{{BASE_JS}}", payload + base_js)
            .replace("{{WORDMARK}}", "")
            .replace("{{ATLAS}}", "")
            .replace("{{SLUG}}", slug)
        )
        (HERE / f"{slug}.html").write_text(page, encoding="utf8", newline="\n")
        print(slug, len(page))


main()
