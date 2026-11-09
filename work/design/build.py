import json,pathlib
here=pathlib.Path(__file__).parent
css=(here/'src/ds.css').read_text(encoding='utf8')
body=(here/'src/ds.html').read_text(encoding='utf8')
js=(here/'src/ds.js').read_text(encoding='utf8')
regions=(here/'regions.min.json').read_text(encoding='utf8')
mark=(here.parent/'brand'/'mark-paths.json').read_text(encoding='utf8')
head='''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<title>Plexus: дизайн-система</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
'''
out=head+'<style>\n'+css+'</style>\n</head>\n<body>\n'+body+'<script>\nconst REGIONS = '+regions+'\nconst MARK = '+mark+'\n'+js+'</script>\n</body>\n</html>\n'
(here/'design-system.html').write_text(out,encoding='utf8',newline='\n')
print(len(out))
