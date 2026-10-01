"""Add new DOI works from Timothy Myers's public ORCID record.

Existing reviewed records are preserved, except when ORCID supplies a newer
version of the same versioned preprint DOI. The scheduled GitHub workflow
presents changes in a pull request for review.
"""
import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS = ROOT / "publications.json"
ORCID = "0000-0003-0582-4554"
USER_AGENT = "tamyers87.github.io publication updater (+https://tamyers87.github.io)"


def fetch_json(url, accept="application/json"):
    request = Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def clean_text(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()


def normalized(value):
    value = unicodedata.normalize("NFKD", clean_text(value)).casefold()
    return "".join(character for character in value if character.isalnum())


def doi_family(doi):
    """Return a DOI identifier with a trailing preprint version removed."""
    return re.sub(r"/v\d+$", "", doi.casefold())


def doi_version(doi):
    """Return the integer from a trailing DOI version, when present."""
    match = re.search(r"/v(\d+)$", doi.casefold())
    return int(match.group(1)) if match else None


def publication_year(metadata, summary):
    parts = metadata.get("issued", {}).get("date-parts", [[]])
    if parts and parts[0]:
        return int(parts[0][0])
    return int(summary["publication-date"]["year"]["value"])


def unique_key(metadata, year, existing_keys):
    authors = metadata.get("author") or []
    family = clean_text(authors[0].get("family")) if authors else "Publication"
    family = re.sub(r"[^A-Za-z0-9]", "", unicodedata.normalize("NFKD", family)) or "Publication"
    stop_words = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "to", "with"}
    words = re.findall(r"[A-Za-z0-9]+", clean_text(metadata.get("title")))
    words = [word for word in words if word.casefold() not in stop_words][:3]
    stem = family + str(year) + "".join(word[0].upper() + word[1:] for word in words)
    key = stem
    suffix = 2
    while key in existing_keys:
        key = f"{stem}{suffix}"
        suffix += 1
    return key


def people(metadata, field):
    result = []
    for person in metadata.get(field) or []:
        family = clean_text(person.get("family"))
        given = clean_text(person.get("given"))
        if family:
            result.append({"family": family, "given": given})
    return result


def record_from_doi(doi, summary, existing_keys):
    metadata = fetch_json(
        "https://doi.org/" + quote(doi, safe="/"),
        "application/vnd.citationstyles.csl+json",
    )
    authors = people(metadata, "author")
    if not any(person["family"].casefold() == "myers" for person in authors):
        raise ValueError(f"DOI metadata does not include Myers: {doi}")

    title = clean_text(metadata.get("title"))
    year = publication_year(metadata, summary)
    orcid_type = summary.get("type", "").replace("-", "_").upper()
    kind = {
        "JOURNAL_ARTICLE": "article",
        "BOOK_CHAPTER": "chapter",
        "PREPRINT": "preprint",
    }.get(orcid_type)
    if kind is None:
        raise ValueError(f"Unsupported ORCID work type {orcid_type}: {doi}")

    record = {
        "source_id": "orcid_" + re.sub(r"[^a-z0-9]+", "_", doi.casefold()).strip("_"),
        "key": unique_key(metadata, year, existing_keys),
        "kind": kind,
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi.casefold(),
        "journal": clean_text(metadata.get("container-title")),
        "volume": clean_text(metadata.get("volume")),
        "number": clean_text(metadata.get("issue")),
        "pages": clean_text(metadata.get("page")),
        "article_number": clean_text(metadata.get("article-number")),
        "publisher": clean_text(metadata.get("publisher")),
    }
    if kind == "chapter":
        record.update({
            "booktitle": clean_text(metadata.get("container-title")),
            "editors": people(metadata, "editor"),
            "chapter": clean_text(metadata.get("chapter-number")),
            "series": clean_text(metadata.get("collection-title")),
        })
    if kind == "preprint":
        record["repository"] = clean_text(metadata.get("publisher")) or "Preprint server"
        record["note"] = "Preprint"
    return record


def orcid_dois():
    record = fetch_json(f"https://pub.orcid.org/v3.0/{ORCID}/works", "application/vnd.orcid+json")
    results = []
    for group in record.get("group", []):
        for summary in group.get("work-summary", []):
            external_ids = (summary.get("external-ids") or {}).get("external-id") or []
            for external_id in external_ids:
                if external_id.get("external-id-type", "").casefold() == "doi":
                    doi = external_id.get("external-id-value", "").strip()
                    if doi:
                        results.append((doi, summary))
    if not results:
        raise RuntimeError("The public ORCID record returned no DOI works.")
    return results


records = json.loads(PUBLICATIONS.read_text())
known_dois = {record["doi"].casefold() for record in records}
known_titles = {normalized(record["title"]) for record in records}
existing_keys = {record["key"] for record in records}
record_by_doi_family = {doi_family(record["doi"]): record for record in records}
added = []
revised = []

for doi, summary in orcid_dois():
    doi = doi.casefold()
    if doi in known_dois:
        continue
    try:
        candidate = record_from_doi(doi, summary, existing_keys)
    except (OSError, ValueError, KeyError) as error:
        print(f"Review manually: {error}")
        continue
    existing = record_by_doi_family.get(doi_family(doi))
    if existing is not None:
        if existing["kind"] != "preprint" or candidate["kind"] != "preprint":
            print(f"Review manually: related DOI already exists: {doi}")
            continue
        existing_version = doi_version(existing["doi"])
        candidate_version = doi_version(candidate["doi"])
        if existing_version is None or candidate_version is None:
            print(f"Review manually: ambiguous preprint DOI revision: {doi}")
            continue
        if candidate_version <= existing_version:
            continue
        old_title = normalized(existing["title"])
        old_doi = existing["doi"].casefold()
        candidate["source_id"] = existing["source_id"]
        candidate["key"] = existing["key"]
        candidate["repository"] = existing.get("repository") or candidate["repository"]
        candidate["note"] = existing.get("note") or candidate["note"]
        existing_authors = [
            normalized(author.get("given", "") + author.get("family", ""))
            for author in existing["authors"]
        ]
        candidate_authors = [
            normalized(author.get("given", "") + author.get("family", ""))
            for author in candidate["authors"]
        ]
        if candidate_authors == existing_authors:
            candidate["authors"] = existing["authors"]
        records[records.index(existing)] = candidate
        known_dois.discard(old_doi)
        known_dois.add(candidate["doi"])
        known_titles.discard(old_title)
        known_titles.add(normalized(candidate["title"]))
        record_by_doi_family[doi_family(doi)] = candidate
        revised.append((old_doi, candidate))
        continue
    if normalized(candidate["title"]) in known_titles:
        continue
    records.append(candidate)
    added.append(candidate)
    known_dois.add(candidate["doi"])
    known_titles.add(normalized(candidate["title"]))
    existing_keys.add(candidate["key"])
    record_by_doi_family[doi_family(doi)] = candidate

if added or revised:
    records.sort(key=lambda item: (-item["year"], item["authors"][0]["family"].casefold(), item["title"].casefold()))
    PUBLICATIONS.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    for record in added:
        print(f"Added: {record['title']} ({record['doi']})")
    for old_doi, record in revised:
        print(f"Revised: {old_doi} -> {record['doi']} ({record['title']})")
else:
    print("No new DOI works found in ORCID.")
