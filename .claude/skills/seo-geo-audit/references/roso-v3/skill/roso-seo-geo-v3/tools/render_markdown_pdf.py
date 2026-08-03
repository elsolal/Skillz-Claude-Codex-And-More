#!/usr/bin/env python3
"""Génère un PDF thémable lisible à partir d'un sous-ensemble Markdown."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfdoc import PDFString
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


NAVY = HexColor("#0E1F3A")
ORANGE = HexColor("#ED8030")
BLUE = HexColor("#3B6ED3")
GREEN = HexColor("#2F9D6A")
RED = HexColor("#D94D4D")
TEXT = HexColor("#24324A")
MUTED = HexColor("#667085")
PALE = HexColor("#F5F7FB")
BORDER = HexColor("#DDE3EC")
COVER_TEXT = HexColor("#FFFFFF")
COVER_MUTED = HexColor("#E4EBF6")
CODE_TEXT = HexColor("#E8ECF5")
BACKGROUND = HexColor("#FFFFFF")
PAGE_SIZE = A4
AGENCY_NAME = "RosoAI"
DOCUMENT_LANGUAGE = "fr-FR"
METHODOLOGY_NAME = "SEO/GEO V3"
METHODOLOGY_VERSION = "3.1.0"
DOCUMENT_DESCRIPTION = "Livrable SEO/GEO fondé sur des preuves"
COVER_SUBTITLE = DOCUMENT_DESCRIPTION
EDITION_LABEL = ""
CONFIDENTIALITY = ""
CONTACT = ""
WEBSITE = ""
FOOTER_LEFT = ""
SHOW_HEADER = True
SHOW_FOOTER = True
SHOW_PAGE_NUMBERS = True
LOGO_PATH: Path | None = None
LOGO_ALT = ""
_TOOL_ROOT = Path(__file__).resolve().parents[1]
_THEME_CANDIDATES = (
    _TOOL_ROOT / "assets" / "default_theme.json",
    _TOOL_ROOT / "skill" / "roso-seo-geo-v3" / "assets" / "default_theme.json",
)
DEFAULT_THEME_PATH = next((candidate for candidate in _THEME_CANDIDATES if candidate.is_file()), _THEME_CANDIDATES[0])


def register_fonts(body_family: str = "Arial", heading_family: str = "Arial") -> tuple[str, str]:
    regular = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    if (body_family.lower() == "arial" or heading_family.lower() == "arial") and regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("RosoSans", str(regular)))
        pdfmetrics.registerFont(TTFont("RosoSans-Bold", str(bold)))

    def resolve(family: str, bold_face: bool) -> str:
        normalized = family.strip().lower()
        if normalized == "arial" and regular.is_file() and bold.is_file():
            return "RosoSans-Bold" if bold_face else "RosoSans"
        if normalized in {"times", "times new roman"}:
            return "Times-Bold" if bold_face else "Times-Roman"
        if normalized in {"courier", "monospace"}:
            return "Courier-Bold" if bold_face else "Courier"
        return "Helvetica-Bold" if bold_face else "Helvetica"

    return resolve(body_family, False), resolve(heading_family, True)


BODY_FONT, BOLD_FONT = register_fonts()


def _merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            result[key] = _merge(base[key], value)
        else:
            result[key] = value
    return result


def load_theme(path: Path | None = None) -> dict:
    try:
        default = json.loads(DEFAULT_THEME_PATH.read_text(encoding="utf-8"))
        custom = json.loads(path.read_text(encoding="utf-8")) if path else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Thème illisible ou JSON invalide: {exc}") from exc
    theme = _merge(default, custom)
    for key in (
        "primary", "accent", "link", "success", "critical", "text", "muted_text",
        "cover_text", "cover_muted_text", "code_text", "background", "soft_background", "border",
    ):
        value = theme.get("colors", {}).get(key)
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError(f"colors.{key} doit être une couleur #RRGGBB")
    agency = theme.get("identity", {}).get("agency_name")
    language = theme.get("identity", {}).get("document_language")
    if not isinstance(agency, str) or not agency.strip() or len(agency) > 100:
        raise ValueError("identity.agency_name doit être un texte non vide de 100 caractères maximum")
    if not isinstance(language, str) or not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", language):
        raise ValueError("identity.document_language doit être un tag tel que fr-FR")
    for key in ("legal_name", "contact", "website", "logo_alt"):
        value = theme.get("identity", {}).get(key)
        if value is not None and (not isinstance(value, str) or len(value) > 240 or any(ord(char) < 32 for char in value)):
            raise ValueError(f"identity.{key} doit être un texte de 240 caractères maximum")
    if theme.get("layout", {}).get("page_size") not in {"A4", "Letter"}:
        raise ValueError("layout.page_size accepte A4 ou Letter")
    if theme.get("layout", {}).get("orientation") not in {"portrait", "landscape"}:
        raise ValueError("layout.orientation accepte portrait ou landscape")
    for key in ("show_header", "show_footer", "show_page_numbers"):
        if not isinstance(theme.get("layout", {}).get(key), bool):
            raise ValueError(f"layout.{key} doit être booléen")
    for key, maximum in (
        ("methodology_name", 100), ("methodology_version", 30), ("description", 240),
        ("cover_subtitle", 300), ("edition_label", 120), ("confidentiality", 160),
        ("footer_left", 160), ("date_format", 40), ("currency", 12), ("units", 40),
    ):
        value = theme.get("document", {}).get(key)
        if not isinstance(value, str) or len(value) > maximum or any(ord(char) < 32 for char in value):
            raise ValueError(f"document.{key} doit être un texte de {maximum} caractères maximum")
    theme["_theme_base_dir"] = str((path.parent if path else DEFAULT_THEME_PATH.parent).resolve())
    return theme


def apply_theme(theme: dict) -> None:
    global NAVY, ORANGE, BLUE, GREEN, RED, TEXT, MUTED, PALE, BORDER, COVER_TEXT, COVER_MUTED, CODE_TEXT, BACKGROUND
    global BODY_FONT, BOLD_FONT, PAGE_SIZE, AGENCY_NAME, DOCUMENT_LANGUAGE, LOGO_PATH, LOGO_ALT
    global METHODOLOGY_NAME, METHODOLOGY_VERSION, DOCUMENT_DESCRIPTION, COVER_SUBTITLE, EDITION_LABEL
    global CONFIDENTIALITY, CONTACT, WEBSITE, FOOTER_LEFT, SHOW_HEADER, SHOW_FOOTER, SHOW_PAGE_NUMBERS
    colors_map = theme["colors"]
    NAVY = HexColor(colors_map["primary"])
    ORANGE = HexColor(colors_map["accent"])
    BLUE = HexColor(colors_map["link"])
    GREEN = HexColor(colors_map["success"])
    RED = HexColor(colors_map["critical"])
    TEXT = HexColor(colors_map["text"])
    MUTED = HexColor(colors_map["muted_text"])
    PALE = HexColor(colors_map["soft_background"])
    BORDER = HexColor(colors_map["border"])
    COVER_TEXT = HexColor(colors_map["cover_text"])
    COVER_MUTED = HexColor(colors_map["cover_muted_text"])
    CODE_TEXT = HexColor(colors_map["code_text"])
    BACKGROUND = HexColor(colors_map["background"])
    BODY_FONT, BOLD_FONT = register_fonts(
        str(theme.get("typography", {}).get("body_family", "Arial")),
        str(theme.get("typography", {}).get("heading_family", "Arial")),
    )
    base_size = A4 if theme["layout"]["page_size"] == "A4" else LETTER
    PAGE_SIZE = landscape(base_size) if theme["layout"]["orientation"] == "landscape" else base_size
    AGENCY_NAME = theme["identity"]["agency_name"].strip()
    DOCUMENT_LANGUAGE = theme["identity"]["document_language"]
    CONTACT = str(theme["identity"].get("contact") or "").strip()
    WEBSITE = str(theme["identity"].get("website") or "").strip()
    document = theme["document"]
    METHODOLOGY_NAME = document["methodology_name"].strip()
    METHODOLOGY_VERSION = document["methodology_version"].strip()
    DOCUMENT_DESCRIPTION = document["description"].strip()
    COVER_SUBTITLE = document["cover_subtitle"].strip()
    EDITION_LABEL = document["edition_label"].strip()
    CONFIDENTIALITY = document["confidentiality"].strip()
    FOOTER_LEFT = document["footer_left"].strip()
    SHOW_HEADER = theme["layout"]["show_header"]
    SHOW_FOOTER = theme["layout"]["show_footer"]
    SHOW_PAGE_NUMBERS = theme["layout"]["show_page_numbers"]
    configured_logo = theme["identity"].get("logo_path")
    LOGO_PATH = None
    LOGO_ALT = str(theme["identity"].get("logo_alt") or f"Logo {AGENCY_NAME}")
    if configured_logo:
        if not isinstance(configured_logo, str) or Path(configured_logo).is_absolute():
            raise ValueError("identity.logo_path doit être relatif au dossier du thème")
        base_dir = Path(theme["_theme_base_dir"])
        candidate = (base_dir / configured_logo).resolve()
        try:
            candidate.relative_to(base_dir)
        except ValueError as exc:
            raise ValueError("identity.logo_path sort du dossier du thème") from exc
        if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Le renderer ReportLab accepte un logo PNG ou JPEG; utiliser le renderer balisé pour SVG")
        if not candidate.is_file() or candidate.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("Logo absent ou supérieur à 2 Mio")
        LOGO_PATH = candidate


def html_color(value) -> str:
    return "#" + value.hexval().replace("0x", "")


def inline_markup(value: str) -> str:
    """Convertit les éléments inline sûrs en balises ReportLab."""
    escaped = html.escape(value.strip())
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda match: (
            f'<link href="{match.group(2)}" color="{html_color(BLUE)}">'
            f"{match.group(1)}</link>"
        ),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"`([^`]+)`", rf'<font name="Courier" color="{html_color(NAVY)}">\1</font>', escaped
    )
    return escaped


class RosoDocTemplate(BaseDocTemplate):
    """Ajoute des signets PDF aux titres."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bookmark_index = 0

    def afterFlowable(self, flowable):  # noqa: N802 - API ReportLab
        if not isinstance(flowable, Paragraph):
            return
        level_by_style = {"Section": 0, "Subsection": 1, "Subsubsection": 2}
        if flowable.style.name not in level_by_style:
            return
        self._bookmark_index += 1
        key = f"heading-{self._bookmark_index}"
        title = flowable.getPlainText()
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level_by_style[flowable.style.name])


def make_styles():
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "CoverKicker",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=9,
            leading=12,
            tracking=2,
            textColor=ORANGE,
            spaceAfter=8,
        ),
        "cover": ParagraphStyle(
            "Cover",
            parent=base["Title"],
            fontName=BOLD_FONT,
            fontSize=35,
            leading=40,
            textColor=COVER_TEXT,
            alignment=TA_LEFT,
            spaceAfter=18,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName=BODY_FONT,
            fontSize=13,
            leading=20,
            textColor=COVER_MUTED,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "Section",
            parent=base["Heading1"],
            fontName=BOLD_FONT,
            fontSize=23,
            leading=28,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=14,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Subsection",
            parent=base["Heading2"],
            fontName=BOLD_FONT,
            fontSize=16,
            leading=20,
            textColor=BLUE,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Subsubsection",
            parent=base["Heading3"],
            fontName=BOLD_FONT,
            fontSize=12,
            leading=15,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9.2,
            leading=13.5,
            textColor=TEXT,
            spaceAfter=7,
            allowWidows=0,
            allowOrphans=0,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9.2,
            leading=13.5,
            textColor=TEXT,
            leftIndent=13,
            firstLineIndent=-8,
            bulletIndent=0,
            spaceAfter=4,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName=BOLD_FONT,
            fontSize=11,
            leading=16,
            textColor=NAVY,
            leftIndent=12,
            rightIndent=8,
            borderColor=ORANGE,
            borderWidth=0,
            borderPadding=8,
            backColor=PALE,
            spaceBefore=5,
            spaceAfter=10,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.4,
            leading=10,
            textColor=CODE_TEXT,
            backColor=NAVY,
            borderPadding=9,
            spaceBefore=4,
            spaceAfter=9,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
        ),
        "table": ParagraphStyle(
            "TableText",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=7.2,
            leading=9.5,
            textColor=TEXT,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName=BOLD_FONT,
            fontSize=7.2,
            leading=9.5,
            textColor=COVER_TEXT,
        ),
    }


def page_decor(canvas, doc):
    width, height = PAGE_SIZE
    canvas.saveState()
    canvas.setTitle(doc.title)
    canvas.setAuthor(doc.author)
    canvas.setSubject(doc.subject)
    canvas._doc.Catalog.Lang = PDFString(DOCUMENT_LANGUAGE)
    if doc.page == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        canvas.setFillColor(ORANGE)
        canvas.rect(0, height - 7 * mm, width, 7 * mm, stroke=0, fill=1)
    else:
        canvas.setStrokeColor(BORDER)
        canvas.setFillColor(MUTED)
        if SHOW_HEADER:
            canvas.line(18 * mm, height - 16 * mm, width - 18 * mm, height - 16 * mm)
            canvas.setFont(BOLD_FONT, 7)
            canvas.drawString(18 * mm, height - 12 * mm, f"{AGENCY_NAME.upper()} · {METHODOLOGY_NAME}")
            canvas.setFont(BODY_FONT, 7)
            canvas.drawRightString(width - 18 * mm, height - 12 * mm, doc.title[:70])
        if SHOW_FOOTER or SHOW_PAGE_NUMBERS:
            canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
            canvas.setFont(BODY_FONT, 7)
            if SHOW_FOOTER:
                canvas.drawString(18 * mm, 10 * mm, FOOTER_LEFT)
            if SHOW_PAGE_NUMBERS:
                canvas.drawRightString(width - 18 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


def split_table_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def code_wrap(value: str, width: int = 92) -> str:
    lines: list[str] = []
    for line in value.splitlines() or [""]:
        if len(line) <= width:
            lines.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.extend(
            textwrap.wrap(
                line,
                width=width,
                subsequent_indent=" " * min(indent + 2, 12),
                replace_whitespace=False,
                drop_whitespace=False,
            )
        )
    return "\n".join(lines)


def parse_markdown(source: str, styles: dict) -> tuple[str, list]:
    lines = source.splitlines()
    title = "RosoAI SEO/GEO V3"
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    story: list = [Spacer(1, 42 * mm)]
    if LOGO_PATH:
        logo = RLImage(str(LOGO_PATH))
        logo._restrictSize(42 * mm, 20 * mm)
        logo.hAlign = "LEFT"
        story.extend([logo, Spacer(1, 7 * mm)])
    story.extend([
        Paragraph(
            f"{html.escape(AGENCY_NAME.upper())} · {html.escape(METHODOLOGY_NAME)} · {html.escape(METHODOLOGY_VERSION)}",
            styles["cover_kicker"],
        ),
        Paragraph(inline_markup(title), styles["cover"]),
        Paragraph(
            html.escape(COVER_SUBTITLE),
            styles["cover_subtitle"],
        ),
        *(
            [Paragraph(html.escape(" · ".join(value for value in (CONTACT, WEBSITE) if value)), styles["cover_subtitle"])]
            if CONTACT or WEBSITE else []
        ),
        Spacer(1, 40 * mm),
        Paragraph(html.escape(" · ".join(value for value in (EDITION_LABEL, CONFIDENTIALITY) if value)), styles["cover_kicker"]),
        PageBreak(),
    ])

    index = 0
    first_h1_skipped = False
    first_section_started = False
    paragraph_buffer: list[str] = []

    def flush_paragraph():
        if paragraph_buffer:
            value = " ".join(item.strip() for item in paragraph_buffer).strip()
            if value:
                story.append(Paragraph(inline_markup(value), styles["body"]))
            paragraph_buffer.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index].rstrip())
                index += 1
            if index < len(lines):
                index += 1
            label = f"{language.upper()}\n" if language else ""
            story.append(Preformatted(label + code_wrap("\n".join(code_lines)), styles["code"]))
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            if not first_h1_skipped:
                first_h1_skipped = True
            else:
                story.extend([PageBreak(), Paragraph(inline_markup(stripped[2:]), styles["h1"])])
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            if first_section_started:
                story.append(PageBreak())
            first_section_started = True
            story.append(Paragraph(inline_markup(stripped[3:]), styles["h1"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:]), styles["h2"]))
            index += 1
            continue
        if stripped.startswith("#### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[5:]), styles["h3"]))
            index += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip().lstrip(">").strip())
                index += 1
            story.append(Paragraph(inline_markup(" ".join(quote_lines)), styles["quote"]))
            continue
        if re.match(r"^[-*] ", stripped) or re.match(r"^\d+[.)] ", stripped):
            flush_paragraph()
            match = re.match(r"^(?:[-*]|\d+[.)])\s+(.*)$", stripped)
            if match:
                marker = "•"
                number = re.match(r"^(\d+)[.)]", stripped)
                if number:
                    marker = f"{number.group(1)}."
                story.append(
                    Paragraph(
                        f"<b>{marker}</b> {inline_markup(match.group(1))}",
                        styles["bullet"],
                    )
                )
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and is_separator_row(lines[index + 1]):
            flush_paragraph()
            rows = [split_table_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_table_row(lines[index]))
                index += 1
            column_count = max(len(row) for row in rows)
            table_data = []
            for row_number, row in enumerate(rows):
                normalized = row + [""] * (column_count - len(row))
                style = styles["table_header"] if row_number == 0 else styles["table"]
                table_data.append([Paragraph(inline_markup(cell), style) for cell in normalized])
            available = PAGE_SIZE[0] - 36 * mm
            table = Table(
                table_data,
                colWidths=[available / column_count] * column_count,
                repeatRows=1,
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                        ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BACKGROUND, PALE]),
                    ]
                )
            )
            story.extend([table, Spacer(1, 8)])
            continue
        if stripped in {"---", "***"}:
            flush_paragraph()
            story.append(Spacer(1, 8))
            index += 1
            continue
        paragraph_buffer.append(stripped)
        index += 1

    flush_paragraph()
    return title, story


def render(input_path: Path, output_path: Path, author: str | None, theme_path: Path | None = None) -> None:
    apply_theme(load_theme(theme_path))
    source = input_path.read_text(encoding="utf-8")
    styles = make_styles()
    title, story = parse_markdown(source, styles)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = RosoDocTemplate(
        str(output_path),
        pagesize=PAGE_SIZE,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=21 * mm,
        bottomMargin=19 * mm,
        title=title,
        author=author or AGENCY_NAME,
        subject=DOCUMENT_DESCRIPTION,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="roso", frames=[frame], onPage=page_decor)])
    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--author")
    parser.add_argument("--theme", type=Path, help="Thème JSON fusionné avec le thème par défaut")
    args = parser.parse_args()
    print(
        "AVERTISSEMENT — outil de contrôle interne.\n"
        "  Ce moteur convertit du Markdown avec sa propre mise en page et sans police embarquée :\n"
        "  son rendu NE SUIT PAS templates/Charte_PDF_RosoAI_V3.md, tombe en repli de police système\n"
        "  et n'est PAS livrable à un client.\n"
        "  Le livrable client est composé en HTML par l'Agent 11, puis imprimé avec tools/render_html_pdf.cjs.\n"
        "  N'utiliser ce moteur que pour relire un rapport de contrôle en interne.",
        file=sys.stderr,
    )
    render(args.input, args.output, args.author, args.theme)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
