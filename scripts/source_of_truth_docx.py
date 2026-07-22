#!/usr/bin/env python3
"""Render / read a project's interim local source-of-truth Word document.

Used by the source-of-truth skill's **local fallback mode** while Atlassian
(Confluence) access is unavailable. Confluence remains the canonical home; this
produces a single `SOURCE_OF_TRUTH.docx` per project in that project's folder as
an interim store, to be migrated to Confluence once access is restored.

Pure Python standard library. Builds the .docx (OpenXML zip) by hand because
Word COM is broken on this machine.

The document is BOTH the human-readable artifact and the data store: on `render`
the structured content model is embedded as `word/sotdata.json` inside the zip so
updates are lossless. `read` returns that embedded model; if it is missing (e.g.
the file was re-saved by Word and dropped the part) it falls back to parsing the
document headings/table so an update can still merge safely.

Usage:
  py source_of_truth_docx.py render --input model.json --output "<folder>\\SOURCE_OF_TRUTH.docx"
  py source_of_truth_docx.py read   --input "<folder>\\SOURCE_OF_TRUTH.docx"   # prints model JSON
  py source_of_truth_docx.py --example --output example.docx

Content model (JSON, all fields optional except title):
{
  "title": "Project name",
  "status": "In Progress",
  "owner": "Dan Yerelian",
  "area": "Membership",
  "target_date": "2026-09-30",
  "key_links": ["SharePoint folder: https://...", "Slack channel: #..."],
  "milestones": ["Kickoff done 2026-07-10", "Pilot launch (target Aug)"],
  "decisions": ["2026-07-21 - Decided X because Y."],
  "risks": ["Open: dependency on Z"],
  "updates": ["2026-07-21 - Created interim local page."]   # reverse-chronological
}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Section heading text -> model key. Order defines render order.
SECTIONS = [
    ("Key Links", "key_links"),
    ("Milestones", "milestones"),
    ("Decisions", "decisions"),
    ("Open Questions / Risks", "risks"),
    ("Updates", "updates"),
]

MIGRATION_NOTE = (
    "Interim local source of truth - pending migration to Confluence "
    "(Atlassian access blocked)."
)


# ---------- xml helpers ----------

def text(value: object) -> str:
    return "" if value is None else str(value)


def xml_text(value: object) -> str:
    return escape(text(value), {'"': "&quot;"})


def run(value: str, *, bold=False, italic=False, size=None, color=None) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if size:
        props.append(f'<w:sz w:val="{size}"/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    prop = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    v = text(value)
    space = ' xml:space="preserve"' if v[:1].isspace() or v[-1:].isspace() else ""
    return f"<w:r>{prop}<w:t{space}>{xml_text(v)}</w:t></w:r>"


def para(runs, *, style=None, bullet=False, spacing_after=120):
    pprops = [f'<w:spacing w:after="{spacing_after}"/>']
    if style:
        pprops.append(f'<w:pStyle w:val="{style}"/>')
    if bullet:
        pprops.append('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')
    if isinstance(runs, str):
        runs = [run(runs)]
    return f"<w:p><w:pPr>{''.join(pprops)}</w:pPr>{''.join(runs)}</w:p>"


def spacer():
    return para([run("")], spacing_after=60)


def _cell(value, *, bold=False, fill=None, width=None):
    tcprops = []
    if width:
        tcprops.append(f'<w:tcW w:w="{width}" w:type="dxa"/>')
    if fill:
        tcprops.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>')
    tcpr = f"<w:tcPr>{''.join(tcprops)}</w:tcPr>" if tcprops else ""
    return (
        f'<w:tc>{tcpr}<w:p><w:pPr><w:spacing w:after="40"/></w:pPr>'
        f"{run(value, bold=bold)}</w:p></w:tc>"
    )


def table(rows, widths=None):
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    if not widths:
        widths = [int(9000 / ncol)] * ncol
    widths = (list(widths) + [widths[-1]] * ncol)[:ncol]
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    body = []
    for r in rows:
        cells = "".join(
            _cell(r[c] if c < len(r) else "", bold=(c == 0),
                  fill=("EDEDED" if c == 0 else None), width=widths[c])
            for c in range(ncol)
        )
        body.append(f"<w:tr>{cells}</w:tr>")
    borders = "<w:tblBorders>" + "".join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        for e in ("top", "left", "bottom", "right", "insideH", "insideV")
    ) + "</w:tblBorders>"
    return (
        '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
        + borders
        + f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>"
        + "".join(body)
        + "</w:tbl>"
    )


# ---------- body assembly ----------

def _list_items(values):
    parts = []
    real = [v for v in (values or []) if text(v).strip()]
    if not real:
        parts.append(para([run("(none yet)", italic=True, color="808080")]))
    else:
        for v in real:
            parts.append(para(text(v), bullet=True))
    return parts


def document_body(data: dict) -> str:
    parts = [para(text(data.get("title") or "Source of Truth"), style="Title")]
    parts.append(para(MIGRATION_NOTE, style="Subtitle"))

    overview = [
        ["Status", text(data.get("status") or "In Progress")],
        ["Owner", text(data.get("owner"))],
        ["Area", text(data.get("area"))],
        ["Target date", text(data.get("target_date"))],
    ]
    parts.append(para("Overview", style="Heading1"))
    summary = text(data.get("overview") or data.get("summary"))
    if summary:
        parts.append(para([run(summary, italic=True)]))
    parts.append(table(overview, widths=[2200, 6800]))
    parts.append(spacer())

    for heading, key in SECTIONS:
        parts.append(para(heading, style="Heading1"))
        parts.extend(_list_items(data.get(key)))
        parts.append(spacer())

    return "\n".join(parts)


# ---------- package parts ----------

def content_types_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="json" ContentType="application/json"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>
"""


def root_rels_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""


def document_rels_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>
"""


def styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/><w:qFormat/>
    <w:rPr><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:after="60"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="34"/><w:color w:val="1F3864"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:after="200"/></w:pPr>
    <w:rPr><w:i/><w:sz w:val="22"/><w:color w:val="C00000"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:before="280" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="1F3864"/></w:rPr>
  </w:style>
</w:styles>
"""


def numbering_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="singleLevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="&#8226;"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>
"""


def document_xml(data: dict):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {document_body(data)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


def create_docx(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml())
        z.writestr("_rels/.rels", root_rels_xml())
        z.writestr("word/_rels/document.xml.rels", document_rels_xml())
        z.writestr("word/document.xml", document_xml(data))
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/numbering.xml", numbering_xml())
        # Lossless data store: the model travels inside the doc.
        z.writestr("word/sotdata.json", json.dumps(data, ensure_ascii=False, indent=2))


# ---------- reading an existing doc ----------

def _q(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _para_text(p_el) -> str:
    return "".join(t.text or "" for t in p_el.iter(_q("t")))


def _para_style(p_el):
    ppr = p_el.find(_q("pPr"))
    if ppr is None:
        return None, False
    style_el = ppr.find(_q("pStyle"))
    style = style_el.get(_q("val")) if style_el is not None else None
    is_bullet = ppr.find(_q("numPr")) is not None
    return style, is_bullet


def parse_docx(path: Path) -> dict:
    """Reconstruct the content model by walking document.xml (fallback reader)."""
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    body = ET.fromstring(xml).find(_q("body"))

    key_by_heading = {h.lower(): k for h, k in SECTIONS}
    data: dict = {"key_links": [], "milestones": [], "decisions": [],
                  "risks": [], "updates": []}
    current = None

    for el in list(body):
        tag = el.tag.split("}")[-1]
        if tag == "tbl":
            for tr in el.findall(_q("tr")):
                cells = [_para_text(tc) for tc in tr.findall(_q("tc"))]
                if len(cells) >= 2:
                    label, value = cells[0].strip().lower(), cells[1].strip()
                    if label == "status":
                        data["status"] = value
                    elif label == "owner":
                        data["owner"] = value
                    elif label == "area":
                        data["area"] = value
                    elif label == "target date":
                        data["target_date"] = value
            continue
        if tag != "p":
            continue
        style, is_bullet = _para_style(el)
        txt = _para_text(el).strip()
        if style == "Title":
            data["title"] = txt
        elif style == "Heading1":
            current = key_by_heading.get(txt.lower())
        elif style == "Subtitle":
            continue
        elif is_bullet and current and txt:
            data[current].append(txt)
    return data


def read_model(path: Path) -> dict:
    """Prefer the embedded JSON model; fall back to parsing the document."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "word/sotdata.json" in names:
            return json.loads(z.read("word/sotdata.json").decode("utf-8"))
    return parse_docx(path)


# ---------- example / cli ----------

EXAMPLE_DATA = {
    "title": "Example Project",
    "status": "In Progress",
    "owner": "Dan Yerelian",
    "area": "Membership",
    "target_date": "2026-09-30",
    "overview": "One-paragraph statement of the outcome / definition of done.",
    "key_links": [
        "SharePoint folder: https://example.sharepoint.com/...",
        "Slack channel: #example-project",
    ],
    "milestones": ["Kickoff complete 2026-07-10", "Pilot launch (target August)"],
    "decisions": ["2026-07-21 - Chose approach A over B for cost reasons."],
    "risks": ["Open: waiting on data access from IT."],
    "updates": ["2026-07-21 - Created interim local source of truth."],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render/read a local source-of-truth .docx")
    parser.add_argument("mode", nargs="?", default="render", choices=["render", "read"])
    parser.add_argument("--input", help="model JSON (render) or existing .docx (read)")
    parser.add_argument("--output", help="path to write .docx (render)")
    parser.add_argument("--example", action="store_true", help="render the example doc")
    args = parser.parse_args()

    try:
        if args.mode == "read":
            if not args.input:
                raise ValueError("read mode needs --input <SOURCE_OF_TRUTH.docx>")
            print(json.dumps(read_model(Path(args.input)), ensure_ascii=False, indent=2))
            return 0

        # render
        if args.example:
            data = EXAMPLE_DATA
        else:
            if not args.input:
                raise ValueError("render mode needs --input <model.json> (or --example)")
            with Path(args.input).open("r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("Input JSON must be an object")
        if not args.output:
            raise ValueError("render mode needs --output <path.docx>")
        create_docx(data, Path(args.output))
        print(f"Wrote {Path(args.output).resolve()}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
