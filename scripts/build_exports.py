"""Generate BibTeX and RIS downloads from publications.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / "publications.json").read_text())
records.sort(key=lambda item: (-item["year"], item["authors"][0]["family"].casefold(), item["title"].casefold()))


def names(people):
    return " and ".join(f"{person['family']}, {person['given']}" for person in people)


def bib_value(value):
    return str(value).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def bib_entry(record):
    entry_type = {"article": "article", "chapter": "incollection", "preprint": "misc"}[record["kind"]]
    fields = [("author", names(record["authors"])), ("title", "{" + record["title"] + "}"), ("year", record["year"])]
    if record["kind"] == "article":
        fields.extend((name, record.get(key, "")) for name, key in (("journal", "journal"), ("volume", "volume"), ("number", "number")))
        fields.append(("pages", (record.get("pages") or record.get("article_number") or "").replace("-", "--")))
    elif record["kind"] == "chapter":
        fields.extend([
            ("booktitle", record.get("booktitle", "")),
            ("editor", names(record.get("editors", []))),
            ("publisher", record.get("publisher", "")),
            ("pages", record.get("pages", "").replace("-", "--")),
            ("chapter", record.get("chapter", "")),
            ("series", record.get("series", "")),
        ])
    else:
        fields.extend([("howpublished", record.get("repository", "Preprint server")), ("note", record.get("note", "Preprint"))])
    if record["kind"] != "preprint" and record.get("note"):
        fields.append(("note", record["note"]))
    fields.extend([("doi", record["doi"]), ("url", "https://doi.org/" + record["doi"])])
    body = ",\n".join(f"  {name} = {{{bib_value(value)}}}" for name, value in fields if value not in (None, ""))
    return f"@{entry_type}{{{record['key']},\n{body}\n}}"


def ris_entry(record):
    entry_type = {"article": "JOUR", "chapter": "CHAP", "preprint": "UNPB"}[record["kind"]]
    lines = [f"TY  - {entry_type}", f"ID  - {record['key']}"]
    lines.extend(f"AU  - {person['family']}, {person['given']}" for person in record["authors"])
    lines.extend([f"TI  - {record['title']}", f"PY  - {record['year']}"])
    if record["kind"] == "article":
        optional = (("JO", record.get("journal")), ("VL", record.get("volume")), ("IS", record.get("number")))
    elif record["kind"] == "chapter":
        optional = (("T2", record.get("booktitle")), ("PB", record.get("publisher")))
        lines.extend(f"ED  - {person['family']}, {person['given']}" for person in record.get("editors", []))
    else:
        optional = (("T2", record.get("repository", "Preprint server")),)
    lines.extend(f"{tag}  - {value}" for tag, value in optional if value)
    pages = record.get("pages") or record.get("article_number") or ""
    match = re.fullmatch(r"(.+?)-(\S+)", pages)
    if match:
        lines.extend([f"SP  - {match.group(1)}", f"EP  - {match.group(2)}"])
    elif pages:
        lines.append(f"SP  - {pages}")
    lines.extend([f"DO  - {record['doi']}", f"UR  - https://doi.org/{record['doi']}"])
    if record.get("note"):
        lines.append(f"N1  - {record['note']}")
    lines.append("ER  - ")
    return "\n".join(lines)


bib_header = "% Timothy A. Myers publication bibliography\n% Generated from the reviewed publications.json file.\n"
(ROOT / "files/Myers_all_publications.bib").write_text(bib_header + "\n\n".join(bib_entry(record) for record in records) + "\n")
(ROOT / "files/Myers_all_publications.ris").write_text("\n\n".join(ris_entry(record) for record in records) + "\n")
print(f"Wrote BibTeX and RIS exports for {len(records)} publications.")
