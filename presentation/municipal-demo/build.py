import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = Path.home() / 'Downloads/Telegram Desktop/plexus-deck.html'
html = source.read_text()
module = re.search(r'(<script type="module"[^>]*>)(.*?)</script>', html, re.S)
bundle = module[2]
patches = {
    '`. Это `,(0,z.jsx)(`span`,{className:`ai-nowrap`,children:`21-е место`}),` из 82`': '`. Рассчитан по дорожной сети.`',

    'mj=480,hj=': 'mj=352,hj=',
    'Что изменится для региона,': 'Где территория теряет доступность',
    'если закрыть дорогу или проложить новую связь': 'и какие изменения дорожной сети помогут',
    'Кейс А2, индекс транспортной связанности': '',
    'async function Y7(e,t,n,r=40){if(!t)return;': 'async function Y7(e,t,n,r=40){r*=.85;if(!t)return;',
    'await e.sleep(x9+6+11)': 'await e.sleep(x9+6+.6)',
    'await e.sleep(17)}}]};': 'await e.sleep(3.9)}}]};',
    'e.animate(t(`map`),[{opacity:1,transform:`none`,filter:`blur(0px)`},{opacity:0,transform:`scale(0.94)`,filter:`blur(2px)`}]': 'e.animate(t(`map`),[{opacity:1,transform:`none`},{opacity:0,transform:`scale(0.94)`}]',
    'children:`99,51`': 'children:`99,15`',
    'd.current=n;let i=new ResizeObserver': 'd.current=n;globalThis.__plexusDemoMap=n;let i=new ResizeObserver',
}
for old, new in patches.items():
    assert old in bundle, old
    bundle = bundle.replace(old, new)
patch = 'const municipalData=' + (ROOT / 'data.json').read_text() + ';\n'
patch += 'const demoRegion=' + (ROOT / 'region.json').read_text() + ';\n'
patch += 'const municipalRoads=' + (ROOT / 'roads.json').read_text() + ';\n'
patch += 'const socialExample=' + (ROOT / 'social-example.json').read_text() + ';\n'
patch += (ROOT / 'reference-scenes.js').read_text()
frames = {name: 'data:image/png;base64,' + base64.b64encode((ROOT / 'road-frames' / (name + '.png')).read_bytes()).decode() for name in ['before', 'closed', 'effect', 'critical']}
patch += '\nconst roadFrames=' + json.dumps(frames) + ';\n'
patch += 'const roadFrameMeta=' + (ROOT / 'road-frames/metadata.json').read_text() + ';\n'
patch += (ROOT / 'road-film.js').read_text()
patch += '\nconst indexMapFrame=' + json.dumps('data:image/png;base64,' + base64.b64encode((ROOT / 'index-map.png').read_bytes()).decode()) + ';\n'
patch += (ROOT / 'index-transition.js').read_text()
patch += (ROOT / 'formula-scene.js').read_text()
patch += '\nconst improvementData=' + (ROOT / 'improvement.json').read_text() + ';\n'
patch += 'const improvementMeta=' + (ROOT / 'improvement-frames/metadata.json').read_text() + ';\n'
improvement_frames = {name: 'data:image/png;base64,' + base64.b64encode((ROOT / 'improvement-frames' / (name + '.png')).read_bytes()).decode() for name in ['neutral', 'before', 'after']}
patch += 'const improvementFrames=' + json.dumps(improvement_frames) + ';\n'
patch += (ROOT / 'improvement-scene.js').read_text()
patch += (ROOT / 'empty-chat-logo.js').read_text()
patch += '\nconst serviceData=' + (ROOT / 'services.json').read_text() + ';\n'
service_frames = {name: 'data:image/png;base64,' + base64.b64encode((ROOT / 'service-frames' / (name + '.png')).read_bytes()).decode() for name in ['neutral', 'N01', 'N04', 'N09']}
patch += 'const serviceFrames=' + json.dumps(service_frames) + ';\n'
patch += '\nconst serviceMeta=' + (ROOT / 'service-frames/metadata.json').read_text() + ';\n'
patch += (ROOT / 'service-scene.js').read_text()

assert bundle.endswith('hye();')
bundle = bundle[:-6] + patch + '\nhye();'
html = html[:module.start(2)] + bundle + html[module.end(2):]
html = html.replace('</head>', '<style>' + (ROOT / 'reference.css').read_text() + '</style></head>')
(ROOT.parent / 'plexus-deck.html').write_text(html)
(ROOT / 'runtime-check.mjs').write_text(bundle)
print('Built original application, assets, cursor and animation engine with mocked municipal scenarios')
