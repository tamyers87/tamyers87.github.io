"""Check generated routes, local links, images, and publication coverage."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()
        self.images = []
        self.publications = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag in ['a', 'link'] and attrs.get('href'):
            self.references.append(attrs['href'])
        if tag in ['img', 'script'] and attrs.get('src'):
            self.references.append(attrs['src'])
        if tag == 'img':
            self.images.append(attrs)
        if tag == 'article' and 'publication' in attrs.get('class', '').split():
            self.publications += 1

pages = {}
for name in ['index.html', 'publications.html', 'cv.html']:
    page = Page()
    content = (DIST / name).read_text()
    page.feed(content)
    assert '<title>' in content and 'name="viewport"' in content, name
    assert 'name="description"' in content and 'application/ld+json' in content, name
    assert ':::' not in content and '### ' not in content, name
    for image in page.images:
        assert image.get('alt'), (name, 'Missing image alt text')
    pages[name] = page

for name, page in pages.items():
    for reference in page.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        path = unquote(url.path)
        target = (DIST / path.lstrip('/')) if path.startswith('/') else (DIST / name).parent / path
        if not path:
            target = DIST / name
        if target.is_dir():
            target /= 'index.html'
        assert target.exists(), (name, reference)
        if url.fragment and target.name in pages:
            assert unquote(url.fragment) in pages[target.name].ids, (name, reference)

records = json.loads((ROOT / 'publications.json').read_text())
page = pages['publications.html']
assert page.publications == len(records)
for item in records:
    assert item['key'] in page.ids
    assert 'https://doi.org/' + item['doi'] in page.references
assert (DIST / 'files/Myers_academic_CV.pdf').read_bytes().startswith(b'%PDF')
assert 'timothy-myers-square.png' in (DIST / 'index.html').read_text()
assert (DIST / 'robots.txt').read_text().strip() == 'Sitemap: https://tamyers87.github.io/sitemap.xml'
assert '<loc>https://tamyers87.github.io/index.html</loc>' in (DIST / 'sitemap.xml').read_text()
print(f'PASS: 3 pages; all local links and assets; {len(records)} publication entries and DOI links; PDF and image references.')
