#!/usr/bin/env node
/** Génère un PDF balisé et une arborescence de signets depuis Markdown. */

const fs = require("fs");
const path = require("path");
const { marked } = require("marked");
const { chromium } = require("playwright");

function pdfUnicodeString(value) {
  const encoded = Buffer.from(String(value), "utf16le");
  for (let index = 0; index < encoded.length; index += 2) {
    const low = encoded[index];
    encoded[index] = encoded[index + 1];
    encoded[index + 1] = low;
  }
  return `<FEFF${encoded.toString("hex").toUpperCase()}>`;
}

function pdfDate(value) {
  const pad = (part) => String(part).padStart(2, "0");
  return `D:${value.getUTCFullYear()}${pad(value.getUTCMonth() + 1)}${pad(value.getUTCDate())}`
    + `${pad(value.getUTCHours())}${pad(value.getUTCMinutes())}${pad(value.getUTCSeconds())}Z`;
}

function appendPdfMetadata(pdfPath, metadata) {
  const payload = fs.readFileSync(pdfPath);
  const source = payload.toString("latin1");
  const trailerOffset = source.lastIndexOf("trailer");
  if (trailerOffset < 0) throw new Error("PDF Chromium invalide: trailer introuvable.");
  const trailerTail = source.slice(trailerOffset);
  const trailerMatch = trailerTail.match(/^trailer\s*<<(.*?)>>\s*startxref\s*(\d+)\s*%%EOF\s*$/s);
  if (!trailerMatch) throw new Error("PDF Chromium invalide: trailer final non reconnu.");
  const trailer = trailerMatch[1];
  const sizeMatch = trailer.match(/\/Size\s+(\d+)/);
  const rootMatch = trailer.match(/\/Root\s+(\d+)\s+(\d+)\s+R/);
  const infoMatch = trailer.match(/\/Info\s+(\d+)\s+(\d+)\s+R/);
  if (!sizeMatch || !rootMatch) throw new Error("PDF Chromium invalide: Size ou Root absent du trailer.");

  const originalSize = Number(sizeMatch[1]);
  const infoObject = infoMatch ? Number(infoMatch[1]) : originalSize;
  const infoGeneration = infoMatch ? Number(infoMatch[2]) : 0;
  const nextSize = infoMatch ? originalSize : originalSize + 1;
  const now = new Date();
  const createdAt = pdfDate(now);
  const fields = [
    ["Title", metadata.title],
    ["Author", metadata.author],
    ["Subject", metadata.subject],
    ["Keywords", metadata.keywords],
    ["Creator", metadata.creator],
    ["Producer", metadata.producer],
    ["CreationDate", createdAt],
    ["ModDate", createdAt],
  ];
  const infoDictionary = fields
    .map(([key, value]) => `/${key} ${pdfUnicodeString(value)}`)
    .join("\n");
  const separator = payload.length && payload[payload.length - 1] === 0x0a ? "" : "\n";
  const objectText = `${separator}${infoObject} ${infoGeneration} obj\n<<\n${infoDictionary}\n>>\nendobj\n`;
  const objectOffset = payload.length + Buffer.byteLength(separator, "latin1");
  const xrefOffset = payload.length + Buffer.byteLength(objectText, "latin1");
  if (objectOffset > 9_999_999_999) throw new Error("PDF trop volumineux pour une table xref classique.");
  const idMatch = trailer.match(/\/ID\s*(\[\s*<[^>]*>\s*<[^>]*>\s*\])/s);
  const xrefText = [
    "xref",
    `${infoObject} 1`,
    `${String(objectOffset).padStart(10, "0")} ${String(infoGeneration).padStart(5, "0")} n `,
    "trailer",
    "<<",
    `/Size ${nextSize}`,
    `/Root ${rootMatch[1]} ${rootMatch[2]} R`,
    `/Info ${infoObject} ${infoGeneration} R`,
    ...(idMatch ? [`/ID ${idMatch[1]}`] : []),
    `/Prev ${trailerMatch[2]}`,
    ">>",
    "startxref",
    String(xrefOffset),
    "%%EOF",
    "",
  ].join("\n");
  fs.appendFileSync(pdfPath, Buffer.from(objectText + xrefText, "latin1"));
}

function usage() {
  console.error("Usage: node render_tagged_pdf.cjs INPUT.md OUTPUT.pdf [--theme THEME.json] [--compact]");
  console.error("Outil de contrôle interne : rendu non conforme à la charte, non livrable au client.");
  console.error("Pour un livrable client, utiliser render_html_pdf.cjs sur le HTML composé par l'Agent 11.");
  process.exit(2);
}

const input = process.argv[2];
const output = process.argv[3];
const compact = process.argv.includes("--compact");
if (!input || !output) usage();

console.error(
  "AVERTISSEMENT — outil de contrôle interne.\n"
  + "  Ce moteur convertit du Markdown en imposant sa propre feuille de style : son rendu NE SUIT PAS\n"
  + "  templates/Charte_PDF_RosoAI_V3.md et n'est PAS livrable à un client.\n"
  + "  Le livrable client est composé en HTML par l'Agent 11, puis imprimé avec tools/render_html_pdf.cjs.\n"
  + "  N'utiliser ce moteur que pour relire un rapport de contrôle en interne."
);

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function merge(base, override) {
  const result = { ...base };
  for (const [key, value] of Object.entries(override || {})) {
    result[key] = value && typeof value === "object" && !Array.isArray(value)
      ? merge(base[key] || {}, value)
      : value;
  }
  return result;
}

function readTheme(themePath) {
  let value;
  try {
    value = JSON.parse(fs.readFileSync(themePath, "utf8"));
  } catch (error) {
    throw new Error(`Thème illisible ou JSON invalide (${themePath}): ${error.message}`);
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`Thème invalide (${themePath}): un objet JSON est attendu.`);
  }
  return value;
}

const defaultThemeCandidates = [
  path.resolve(__dirname, "../assets/default_theme.json"),
  path.resolve(__dirname, "../skill/roso-seo-geo-v3/assets/default_theme.json"),
];
const defaultThemePath = defaultThemeCandidates.find((candidate) => fs.existsSync(candidate));
if (!defaultThemePath) throw new Error("Thème par défaut introuvable dans le Skill ou le package.");
const themeOptionIndex = process.argv.indexOf("--theme");
if (themeOptionIndex >= 0 && !process.argv[themeOptionIndex + 1]) usage();
const customThemePath = themeOptionIndex >= 0 ? path.resolve(process.argv[themeOptionIndex + 1]) : null;
const theme = merge(readTheme(defaultThemePath), customThemePath ? readTheme(customThemePath) : {});
const themeBaseDir = path.dirname(customThemePath || defaultThemePath);

function color(name) {
  const value = theme.colors?.[name];
  if (typeof value !== "string" || !/^#[0-9a-fA-F]{6}$/.test(value)) {
    throw new Error(`Thème invalide: colors.${name} doit être une couleur hexadécimale #RRGGBB.`);
  }
  return value.toLowerCase();
}

for (const requiredColor of [
  "primary", "accent", "link", "success", "critical", "text", "muted_text",
  "cover_text", "cover_muted_text", "code_text", "background", "soft_background", "border",
]) color(requiredColor);

function label(name, value, maximum = 100) {
  if (typeof value !== "string" || !value.trim() || value.length > maximum || /[\u0000-\u001f]/.test(value)) {
    throw new Error(`Thème invalide: ${name} doit être un texte non vide de ${maximum} caractères maximum.`);
  }
  return value.trim();
}

function fontFamily(name, value) {
  const family = label(name, value, 80);
  if (!/^[A-Za-z0-9 À-ÿ,'"._-]+$/.test(family)) {
    throw new Error(`Thème invalide: ${name} contient des caractères non autorisés.`);
  }
  return family;
}

function optionalLabel(name, value, maximum = 240) {
  if (value === null || value === undefined || value === "") return "";
  return label(name, value, maximum);
}

const agencyName = label("identity.agency_name", theme.identity?.agency_name || "RosoAI");
const legalName = optionalLabel("identity.legal_name", theme.identity?.legal_name || agencyName);
const authorOrganization = [...new Set([agencyName, legalName].filter(Boolean))].join(" / ");
const contact = optionalLabel("identity.contact", theme.identity?.contact);
const website = optionalLabel("identity.website", theme.identity?.website);
const documentLanguage = label("identity.document_language", theme.identity?.document_language || "fr-FR", 20);
if (!/^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/.test(documentLanguage)) {
  throw new Error("Thème invalide: identity.document_language doit être un tag de langue simple, par exemple fr-FR.");
}
const headingFont = fontFamily("typography.heading_family", theme.typography?.heading_family || "Arial");
const bodyFont = fontFamily("typography.body_family", theme.typography?.body_family || "Arial");
const codeFont = fontFamily("typography.code_family", theme.typography?.code_family || "monospace");
const methodologyName = label("document.methodology_name", theme.document?.methodology_name || "SEO/GEO V3", 100);
const methodologyVersion = label("document.methodology_version", theme.document?.methodology_version || "3.0.0", 30);
const documentDescription = label("document.description", theme.document?.description || "Livrable SEO/GEO fondé sur des preuves", 240);
const coverSubtitle = label("document.cover_subtitle", theme.document?.cover_subtitle || documentDescription, 300);
const editionLabel = optionalLabel("document.edition_label", theme.document?.edition_label, 120);
const confidentiality = optionalLabel("document.confidentiality", theme.document?.confidentiality, 160);
const footerLeft = optionalLabel("document.footer_left", theme.document?.footer_left, 160);
const dateFormat = optionalLabel("document.date_format", theme.document?.date_format, 40);
const currency = optionalLabel("document.currency", theme.document?.currency, 12);
const units = optionalLabel("document.units", theme.document?.units, 40);
const pageSize = theme.layout?.page_size || "A4";
const orientation = theme.layout?.orientation || "portrait";
if (!new Set(["A4", "Letter"]).has(pageSize) || !new Set(["portrait", "landscape"]).has(orientation)) {
  throw new Error("Thème invalide: layout accepte A4/Letter et portrait/landscape.");
}
for (const key of ["show_header", "show_footer", "show_page_numbers"]) {
  if (typeof theme.layout?.[key] !== "boolean") throw new Error(`Thème invalide: layout.${key} doit être booléen.`);
}
const showHeader = theme.layout.show_header;
const showFooter = theme.layout.show_footer;
const showPageNumbers = theme.layout.show_page_numbers;
const dimensions = {
  "A4:portrait": [210, 297], "A4:landscape": [297, 210],
  "Letter:portrait": [215.9, 279.4], "Letter:landscape": [279.4, 215.9],
}[`${pageSize}:${orientation}`];

function embeddedLogo() {
  const configured = theme.identity?.logo_path;
  if (configured === null || configured === undefined || configured === "") return "";
  if (typeof configured !== "string" || path.isAbsolute(configured)) {
    throw new Error("Thème invalide: identity.logo_path doit être un chemin relatif au dossier du thème.");
  }
  const resolved = path.resolve(themeBaseDir, configured);
  const relative = path.relative(themeBaseDir, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Thème invalide: identity.logo_path sort du dossier du thème.");
  }
  const mimeByExtension = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml" };
  const mime = mimeByExtension[path.extname(resolved).toLowerCase()];
  if (!mime) throw new Error("Thème invalide: le logo doit être PNG, JPEG ou SVG.");
  let payload;
  try {
    payload = fs.readFileSync(resolved);
  } catch (error) {
    throw new Error(`Logo illisible (${resolved}): ${error.message}`);
  }
  if (payload.length > 2 * 1024 * 1024) throw new Error("Thème invalide: le logo dépasse 2 Mio.");
  const alt = label("identity.logo_alt", theme.identity?.logo_alt || `Logo ${agencyName}`, 160);
  return `<img class="brand-logo" src="data:${mime};base64,${payload.toString("base64")}" alt="${escapeHtml(alt)}">`;
}

const logoMarkup = embeddedLogo();

const markdown = fs.readFileSync(input, "utf8");
const titleMatch = markdown.match(/^#\s+(.+)$/m);
const title = titleMatch ? titleMatch[1].trim() : "RosoAI SEO/GEO V3";
let withoutTitle = titleMatch
  ? markdown.replace(titleMatch[0], "")
  : markdown;

// La liste de métadonnées d'en-tête devient le bandeau de traçabilité de la couverture.
const coverFacts = [];
const leadingList = withoutTitle.match(/^\s*((?:[ \t]*-[ \t]+[^\n]+\n?)+)/);
if (leadingList) {
  const parsed = leadingList[1]
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const item = line.replace(/^-[ \t]+/, "");
      const separator = item.indexOf(" : ");
      if (separator < 0) return null;
      return {
        label: item.slice(0, separator).trim(),
        value: item.slice(separator + 3).trim().replace(/`/g, ""),
      };
    });
  if (parsed.length >= 2 && parsed.every(Boolean)) {
    coverFacts.push(...parsed);
    withoutTitle = withoutTitle.replace(leadingList[1], "");
  }
}

// Les identifiants longs vont dans la ligne de traçabilité ; la grille garde quatre colonnes lisibles.
const traceFacts = coverFacts.filter((fact) => fact.value.length > 28 && !/\s/.test(fact.value));
const gridFacts = coverFacts.filter((fact) => !traceFacts.includes(fact)).slice(0, 4);

marked.use({
  gfm: true,
  breaks: false,
  renderer: Object.assign(new marked.Renderer(), {
    html: ({ text }) => escapeHtml(text),
  }),
});

const article = marked.parse(withoutTitle);
const html = `<!doctype html>
<html lang="${escapeHtml(documentLanguage)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:">
<meta name="author" content="${escapeHtml(agencyName)}">
<meta name="description" content="${escapeHtml(documentDescription)}">
<meta name="publisher" content="${escapeHtml(legalName)}">
<meta name="contact" content="${escapeHtml(contact)}">
<meta name="date-format" content="${escapeHtml(dateFormat)}">
<meta name="currency" content="${escapeHtml(currency)}">
<meta name="units" content="${escapeHtml(units)}">
<title>${escapeHtml(title)}</title>
<style>
  :root {
    --navy:${color("primary")}; --orange:${color("accent")}; --blue:${color("link")};
    --green:${color("success")}; --red:${color("critical")}; --text:${color("text")};
    --muted:${color("muted_text")}; --cover-text:${color("cover_text")};
    --cover-muted:${color("cover_muted_text")}; --code-text:${color("code_text")};
    --background:${color("background")}; --pale:${color("soft_background")}; --border:${color("border")};
    --heading-font:${JSON.stringify(headingFont)}; --body-font:${JSON.stringify(bodyFont)}; --code-font:${JSON.stringify(codeFont)};
  }
  * { box-sizing:border-box; }
  @page { size:${pageSize} ${orientation}; margin:24mm 18mm 23mm; }
  @page :first { margin:0; }
  html { font-family:var(--body-font), "Helvetica Neue", Arial, Helvetica, sans-serif; color:var(--text); font-size:10.5pt; line-height:1.55; }
  body { margin:0; background:var(--background); }

  /* ---------- Couverture pleine page ---------- */
  .cover {
    width:${dimensions[0]}mm; height:${dimensions[1]}mm; margin:0; padding:26mm 22mm 22mm;
    color:var(--cover-text); background:var(--navy);
    break-after:page; display:flex; flex-direction:column; justify-content:space-between;
  }
  .cover .brand-logo { display:block; max-width:42mm; max-height:18mm; object-fit:contain; object-position:left center; }
  .cover .cover-brand { font-family:var(--heading-font), Arial, sans-serif; font-size:15pt; font-weight:800; letter-spacing:.01em; color:var(--cover-text); }
  .cover .kicker { color:var(--cover-muted); font-weight:700; font-size:8.5pt; letter-spacing:.18em; text-transform:uppercase; }
  .cover h1 { margin:6mm 0 6mm; color:var(--cover-text); font-size:33pt; line-height:1.06; letter-spacing:-.01em; max-width:158mm; }
  .cover .subtitle { max-width:145mm; color:var(--cover-muted); font-size:12pt; line-height:1.6; margin:0; }
  .cover .cover-rule { height:.25mm; background:var(--cover-muted); opacity:.45; margin:9mm 0 6mm; }
  .cover .cover-facts { display:grid; grid-template-columns:repeat(auto-fit, minmax(34mm, 1fr)); gap:6mm 8mm; margin:0; }
  .cover .cover-facts dt { color:var(--cover-muted); font-size:7pt; font-weight:700; letter-spacing:.14em; text-transform:uppercase; margin:0 0 1.6mm; }
  .cover .cover-facts dd { margin:0; color:var(--cover-text); font-size:9.5pt; font-weight:700; line-height:1.35; overflow-wrap:anywhere; }
  .cover .cover-foot { color:var(--cover-muted); font-size:8pt; }
  .cover .cover-foot .trace { margin:0 0 2.5mm; font-family:var(--code-font), Menlo, monospace; font-size:7pt; opacity:.85; overflow-wrap:anywhere; }
  .cover .cover-foot .identity { margin:0 0 2.5mm; }
  .cover .cover-foot .edition { margin:0; font-weight:700; letter-spacing:.12em; text-transform:uppercase; font-size:7.5pt; }

  /* ---------- Sections ---------- */
  main { display:block; counter-reset:section; }
  article > h2 { break-before:${compact ? "auto" : "page"}; }
  article > h2.first-section { break-before:auto; }
  h1, h2, h3, h4 { font-family:var(--heading-font), "Helvetica Neue", Arial, Helvetica, sans-serif; }
  h2 {
    color:var(--navy); font-size:25pt; line-height:1.12; letter-spacing:-.01em;
    margin:0 0 4mm; padding:0; max-width:160mm;
  }
  article > h2::before {
    counter-increment:section;
    content:"Partie " counter(section, decimal-leading-zero);
    display:table; margin:0 0 5mm; padding:2mm 4mm;
    background:var(--pale); color:var(--blue); border-radius:1.5mm;
    font-size:8pt; font-weight:800; letter-spacing:.16em; text-transform:uppercase;
  }
  article > h2::after { content:""; display:block; width:16mm; height:1mm; background:var(--orange); margin:4mm 0 0; }
  h3 {
    color:var(--navy); font-size:14pt; line-height:1.25; margin:8mm 0 3mm;
    padding-top:3.5mm; border-top:.25mm solid var(--border);
  }
  h4 { color:var(--navy); font-size:11pt; line-height:1.3; margin:5mm 0 2mm; }
  p { margin:0 0 3.4mm; orphans:3; widows:3; }
  strong { color:var(--navy); }
  a { color:var(--blue); text-decoration:underline; text-underline-offset:1px; }
  ul, ol { margin:2mm 0 4.5mm 5mm; padding-left:4mm; }
  li { margin:0 0 1.8mm; break-inside:avoid; }
  li::marker { color:var(--blue); }

  /* ---------- Grille de métadonnées (remplace les listes « Clé : valeur ») ---------- */
  .meta-grid {
    display:grid; grid-template-columns:repeat(auto-fit, minmax(42mm, 1fr));
    gap:0; margin:2mm 0 5mm; border:.25mm solid var(--border); border-radius:2mm; overflow:hidden;
    break-inside:avoid;
  }
  .meta-grid > div { padding:2.8mm 3.5mm; border-top:.25mm solid var(--border); border-left:.25mm solid var(--border); }
  .meta-grid > div:nth-child(-n+3) { border-top:0; }
  .meta-grid dt { color:var(--muted); font-size:6.8pt; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin:0 0 1.2mm; }
  .meta-grid dd { margin:0; color:var(--navy); font-size:9pt; font-weight:700; line-height:1.3; overflow-wrap:anywhere; }
  .meta-grid dd code { background:transparent; padding:0; font-size:8.2pt; }

  /* ---------- Encadrés ---------- */
  blockquote {
    margin:5mm 0; padding:4.5mm 5.5mm; border-left:1.2mm solid var(--orange);
    background:var(--pale); border-radius:0 2mm 2mm 0; color:var(--navy); font-weight:700;
    break-inside:avoid;
  }
  blockquote p:last-child { margin-bottom:0; }
  code { font-family:var(--code-font), Menlo, Consolas, monospace; font-size:.88em; color:var(--navy); background:var(--pale); padding:.3mm 1mm; border-radius:1mm; }
  pre { white-space:pre-wrap; overflow-wrap:anywhere; break-inside:avoid; margin:3mm 0 5mm; padding:4.5mm; color:var(--code-text); background:var(--navy); border-radius:2mm; font-size:8pt; line-height:1.5; }
  pre code { color:inherit; background:transparent; padding:0; }

  /* ---------- Tableaux ---------- */
  table {
    width:100%; border-collapse:separate; border-spacing:0; table-layout:fixed;
    margin:3mm 0 6mm; font-size:8.6pt; break-inside:auto;
    border:.25mm solid var(--border); border-radius:2mm; overflow:hidden;
  }
  thead { display:table-header-group; }
  tr { break-inside:avoid; }
  th {
    padding:3mm 3.2mm; color:var(--cover-text); background:var(--navy);
    text-align:left; vertical-align:top; font-size:8.6pt; font-weight:700; border:0;
  }
  td { padding:3mm 3.2mm; border:0; border-top:.25mm solid var(--border); text-align:left; vertical-align:top; overflow-wrap:anywhere; }
  tbody tr:nth-child(even) { background:var(--pale); }
  td code { font-size:8pt; }
  hr { border:0; border-top:.25mm solid var(--border); margin:7mm 0; }
  img { max-width:100%; height:auto; }
  @media print {
    a { color:var(--blue); }
    h2, h3, h4 { break-after:avoid; }
  }
</style>
</head>
<body>
  <section class="cover" aria-labelledby="cover-title">
    ${logoMarkup || `<div class="cover-brand">${escapeHtml(agencyName)}</div>`}
    <div class="cover-main">
      <div class="kicker">${escapeHtml([methodologyName, methodologyVersion].filter(Boolean).join(" · "))}</div>
      <h1 id="cover-title">${escapeHtml(title)}</h1>
      <p class="subtitle">${escapeHtml(coverSubtitle)}</p>
      ${gridFacts.length ? `<div class="cover-rule"></div>
      <dl class="cover-facts">${gridFacts
        .map((fact) => `<div><dt>${escapeHtml(fact.label)}</dt><dd>${escapeHtml(fact.value)}</dd></div>`)
        .join("")}</dl>` : ""}
    </div>
    <div class="cover-foot">
      ${traceFacts.length ? `<p class="trace">${traceFacts
        .map((fact) => `${escapeHtml(fact.label)} : ${escapeHtml(fact.value)}`)
        .join(" · ")}</p>` : ""}
      ${(contact || website) ? `<p class="identity">${escapeHtml([contact, website].filter(Boolean).join(" · "))}</p>` : ""}
      <p class="edition">${escapeHtml([editionLabel, confidentiality].filter(Boolean).join(" · "))}</p>
    </div>
  </section>
  <main><article>${article}</article></main>
</body>
</html>`;

(async () => {
  fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
  const configuredBrowser = process.env.ROSO_CHROME_PATH;
  if (configuredBrowser && !fs.existsSync(configuredBrowser)) {
    throw new Error(`ROSO_CHROME_PATH pointe vers un fichier absent: ${configuredBrowser}`);
  }
  const macChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const executablePath = configuredBrowser || (fs.existsSync(macChrome) ? macChrome : undefined);
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  try {
    const page = await browser.newPage();
    await page.route("**/*", (route) => route.abort());
    await page.setContent(html, { waitUntil: "load" });
    await page.evaluate(() => {
      const firstSection = document.querySelector("article > h2");
      if (firstSection) firstSection.classList.add("first-section");
      for (const table of document.querySelectorAll("table")) {
        for (const cell of table.querySelectorAll("thead th")) cell.setAttribute("scope", "col");
      }
      // Une liste dont chaque entrée est « Libellé : valeur » devient une grille lisible.
      for (const list of document.querySelectorAll("article ul")) {
        const items = [...list.children].filter((node) => node.tagName === "LI");
        if (items.length < 3 || items.some((item) => item.querySelector("ul, ol, p, table"))) continue;
        const pairs = items.map((item) => {
          const text = item.textContent || "";
          const separator = text.indexOf(" : ");
          if (separator < 1 || separator > 44) return null;
          const label = text.slice(0, separator).trim();
          if (!label || /[.!?]$/.test(label)) return null;
          return { label, value: text.slice(separator + 3).trim(), node: item };
        });
        if (pairs.some((pair) => pair === null)) continue;
        const grid = document.createElement("dl");
        grid.className = "meta-grid";
        for (const pair of pairs) {
          const cell = document.createElement("div");
          const term = document.createElement("dt");
          term.textContent = pair.label;
          const detail = document.createElement("dd");
          const inlineCode = pair.node.querySelector("code");
          if (inlineCode && inlineCode.textContent.trim() === pair.value) {
            const codeNode = document.createElement("code");
            codeNode.textContent = pair.value;
            detail.appendChild(codeNode);
          } else {
            detail.textContent = pair.value;
          }
          cell.append(term, detail);
          grid.appendChild(cell);
        }
        list.replaceWith(grid);
      }
    });
    await page.emulateMedia({ media: "print" });
    const outputPath = path.resolve(output);
    await page.pdf({
      path: outputPath,
      format: pageSize,
      landscape: orientation === "landscape",
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: showHeader || showFooter || showPageNumbers,
      tagged: true,
      outline: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
      headerTemplate: showHeader
        ? `<div style="width:100%;height:100%;overflow:hidden;display:flex;align-items:flex-end"><div style="width:100%;padding:0 18mm 8mm;color:${color("muted_text")};font-size:6.5px;letter-spacing:1.3px;text-transform:uppercase;font-weight:700;font-family:${escapeHtml(bodyFont)},Arial,sans-serif;display:flex;justify-content:space-between"><span>${escapeHtml(agencyName)} · ${escapeHtml(methodologyName)}</span><span>${escapeHtml(title)}</span></div></div>`
        : "<div></div>",
      footerTemplate: (showFooter || showPageNumbers)
        ? `<div style="width:100%;height:100%;overflow:hidden;display:flex;align-items:flex-start"><div style="width:100%;padding:5mm 18mm 0;color:${color("muted_text")};font-size:7px;font-family:${escapeHtml(bodyFont)},Arial,sans-serif;display:flex;justify-content:space-between"><span>${showFooter ? escapeHtml(footerLeft) : ""}</span>${showPageNumbers ? '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span>' : ""}</div></div>`
        : "<div></div>",
    });
    appendPdfMetadata(outputPath, {
      title,
      author: authorOrganization,
      subject: documentDescription,
      keywords: `${methodologyName}; version ${methodologyVersion}`,
      creator: `${agencyName} - ${methodologyName} ${methodologyVersion}`,
      producer: `${agencyName} PDF renderer (Chromium/Playwright)`,
    });
  } finally {
    await browser.close();
  }
  console.log(path.resolve(output));
})().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
