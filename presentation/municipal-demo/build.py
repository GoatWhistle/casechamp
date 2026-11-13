import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Downloads/Telegram Desktop/plexus-deck.html'
html = source.read_text()
module = re.search(r'(<script type="module"[^>]*>)(.*?)</script>', html, re.S)
if module is None:
    raise RuntimeError('Presentation module not found')
bundle = module[2]
replacements = {
    'setTimeout(n,e*1e3);this.wakers.add(n)': 'setTimeout(n,e*350);this.wakers.add(n)',
    'duration:Math.max(1,n.dur*1e3),delay:(n.delay??0)*1e3': 'duration:Math.max(1,n.dur*350),delay:(n.delay??0)*350',
    'o=performance.now()+r*1e3': 'o=performance.now()+r*350',
    'let r=(n-o)/(e*1e3)': 'let r=(n-o)/(e*350)',
    'Что изменится для региона,': 'Доступность Ставропольского края.',
    'если закрыть дорогу или проложить новую связь': 'От муниципалитета до конкретного места.',
    '(0,z.jsx)(f_e,{})': 'null',
}
for old, new in replacements.items():
    if old not in bundle:
        raise RuntimeError('Missing patch anchor: ' + old)
    bundle = bundle.replace(old, new)
start = bundle.index('async function hye(){for(')
end = bundle.index('Mj.load($9);', start)
bundle = bundle[:start] + 'async function hye(){' + bundle[end:]
data = 'const municipalData=' + (ROOT / 'data.json').read_text() + ';\n'
patch = data + (ROOT / 'scenes.js').read_text() + '\n' + (ROOT / 'road-scene.js').read_text()
assert bundle.endswith('hye();')
bundle = bundle[:-6] + patch + '\nhye();'
html = html[:module.start(2)] + bundle + html[module.end(2):]
html = re.sub(r'<script type="text/plain" id="(?:rec-[^"]+|tile-pack)"[^>]*>.*?</script>', '', html, flags=re.S)
css = (ROOT / 'demo.css').read_text()
html = html.replace('</head>', '<style>' + css + '</style>\n</head>')
html = html.replace('<title>Plexus</title>', '<title>Plexus | Муниципалитеты Ставропольского края</title>')
output = ROOT.parent / 'plexus-deck.html'
output.write_text(html)
(ROOT / 'runtime-check.mjs').write_text(bundle)
print(f'Built {output}: {output.stat().st_size:,} bytes')
