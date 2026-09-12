"""Build the publication page from reviewed metadata using only Python's standard library."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'publications.json').read_text())
records.sort(key=lambda item: (-item['year'], item['authors'][0]['family'].casefold(), item['title'].casefold()))

def escape(value):
    return html.escape(str(value), quote=True)

def author_name(person):
    initials = ' '.join('-'.join(part[0] + '.' for part in word.split('-') if part) for word in person['given'].split())
    name = escape(initials + ' ' + person['family'])
    if person['family'] == 'Myers' and person['given'].startswith(('T.', 'Timothy')):
        return '<strong>' + name + '</strong>'
    return name

def publication(record):
    names = ', '.join(author_name(person) for person in record['authors'])
    if record['kind'] == 'article':
        venue = '<em>' + escape(record['journal']) + '</em>'
        if record['volume']:
            venue += ', <strong>' + escape(record['volume']) + '</strong>'
        if record['number']:
            venue += '(' + escape(record['number']) + ')'
        pages = record['pages'] or record['article_number']
        if pages:
            venue += ', ' + escape(pages.replace('-', '–'))
        if record.get('note'):
            venue += ' · ' + escape(record['note'])
    elif record['kind'] == 'chapter':
        editors = ', '.join(author_name(person) for person in record['editors'])
        venue = 'In ' + editors + ' (ed' + ('s' if len(record['editors']) > 1 else '') + '.), <em>' + escape(record['booktitle']) + '</em>'
        venue += ', pp. ' + escape(record['pages'].replace('-', '–')) + '. ' + escape(record['publisher'])
    else:
        repository = record.get('repository') or 'Preprint server'
        venue = '<span class="preprint-label">Preprint</span> ' + escape(repository)
    return f'''<article class="publication" id="{escape(record['key'])}">
<h3><a href="https://doi.org/{escape(record['doi'])}">{escape(record['title'])}</a></h3>
<p class="pub-authors">{names} ({record['year']}).</p>
<p class="pub-venue">{venue}.</p>
<p class="pub-doi"><a href="https://doi.org/{escape(record['doi'])}">doi:{escape(record['doi'])}</a></p>
</article>'''

counts = {kind: sum(record['kind'] == kind for record in records) for kind in ('article', 'chapter', 'preprint')}
count_line = f"{counts['article']} journal articles · {counts['chapter']} book chapters · {counts['preprint']} preprints"

parts = [f'''---
title: Publications
description: "Journal articles, book chapters, and preprints by Timothy A. Myers."
---

::: {{.publication-intro}}
{count_line}

[Google Scholar](https://scholar.google.com/citations?user=nzdByNgAAAAJ&hl=en) · [BibTeX](files/Myers_all_publications.bib) · [RIS](files/Myers_all_publications.ris)

[Journal articles](#journal-articles) · [Book chapters](#book-chapters) · [Preprints](#preprints)
:::

''']
for kind, heading, section_id in [('article', 'Journal articles', 'journal-articles'), ('chapter', 'Book chapters', 'book-chapters'), ('preprint', 'Preprints', 'preprints')]:
    parts.append(f'## {heading} {{#{section_id}}}\n')
    selected = [record for record in records if record['kind'] == kind]
    last_year = None
    for record in selected:
        if kind == 'article' and record['year'] != last_year:
            parts.append(f'\n### {record["year"]} {{.publication-year}}\n')
            last_year = record['year']
        parts.append('\n```{=html}\n' + publication(record) + '\n```\n')
(ROOT / 'publications.qmd').write_text('\n'.join(parts))
print(f'Wrote {len(records)} publications.')
