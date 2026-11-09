import base64
import os
import pathlib

here = pathlib.Path(__file__).parent
onest = pathlib.Path(os.environ["ONEST_DIR"])


def face(file: str, unicode_range: str) -> str:
    data = base64.b64encode((onest / file).read_bytes()).decode()
    return (
        "@font-face{font-family:'Onest';font-style:normal;font-display:block;font-weight:100 900;"
        f"src:url(data:font/woff2;base64,{data}) format('woff2');unicode-range:{unicode_range};}}\n"
    )


fonts = face("onest-cyrillic-wght-normal.woff2", "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116") + face(
    "onest-latin-wght-normal.woff2", "U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+2212,U+FEFF"
)
src = here / "src"
page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<title>Plexus: знак</title>
<style>
{fonts}{(src / "page.css").read_text(encoding="utf8")}</style>
</head>
<body>
{(src / "page.html").read_text(encoding="utf8")}<script>
{(src / "marks.js").read_text(encoding="utf8")}
{(src / "page.js").read_text(encoding="utf8")}</script>
</body>
</html>
"""
(here / "plexus.html").write_text(page, encoding="utf8", newline="\n")
print(len(page))
