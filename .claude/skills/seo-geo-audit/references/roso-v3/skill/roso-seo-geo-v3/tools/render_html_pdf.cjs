#!/usr/bin/env node
/**
 * Imprime en PDF A4 balisé le HTML composé par l'Agent 11.
 *
 * Ce moteur n'ajoute aucun style et ne modifie jamais la mise en page : il imprime
 * exactement ce que l'agent a composé en suivant templates/Charte_PDF_RosoAI_V3.md.
 * Il refuse de rendre un HTML qui violerait les contraintes de la charte.
 */

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");
const { localFileAllowed } = require("./local_file_policy.cjs");

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

/**
 * Relève la pagination réelle depuis les signets du PDF de première passe.
 * Retourne une table « titre du signet » -> numéro de page, pour alimenter le sommaire.
 */
function outlinePageMap(pdfBuffer) {
  const source = pdfBuffer.toString("latin1");
  const objects = new Map();
  for (const match of source.matchAll(/(\d+) 0 obj([\s\S]*?)endobj/g)) {
    objects.set(Number(match[1]), match[2]);
  }
  const catalog = [...objects.entries()].find(([, body]) => /\/Type\s*\/Catalog/.test(body));
  if (!catalog) return new Map();
  const pagesRef = catalog[1].match(/\/Pages\s+(\d+) 0 R/);
  const outlinesRef = catalog[1].match(/\/Outlines\s+(\d+) 0 R/);
  if (!pagesRef || !outlinesRef) return new Map();

  const order = [];
  const walkPages = (objectNumber, seen = new Set()) => {
    if (seen.has(objectNumber)) return;
    seen.add(objectNumber);
    const body = objects.get(objectNumber);
    if (!body) return;
    if (/\/Type\s*\/Page[^s]/.test(body)) { order.push(objectNumber); return; }
    const kids = body.match(/\/Kids\s*\[([\s\S]*?)\]/);
    if (!kids) return;
    for (const kid of kids[1].matchAll(/(\d+) 0 R/g)) walkPages(Number(kid[1]), seen);
  };
  walkPages(Number(pagesRef[1]));
  const pageNumber = new Map(order.map((objectNumber, index) => [objectNumber, index + 1]));

  const decodeTitle = (raw) => {
    if (raw.startsWith("<")) {
      const hex = raw.slice(1, -1).replace(/\s+/g, "");
      const bytes = Buffer.from(hex, "hex");
      if (bytes[0] === 0xfe && bytes[1] === 0xff) return bytes.subarray(2).swap16().toString("utf16le");
      return bytes.toString("latin1");
    }
    return raw.slice(1, -1).replace(/\\([()\\])/g, "$1");
  };

  const map = new Map();
  const walkOutline = (objectNumber, seen = new Set()) => {
    while (objectNumber && !seen.has(objectNumber)) {
      seen.add(objectNumber);
      const body = objects.get(objectNumber);
      if (!body) return;
      const title = body.match(/\/Title\s*(\([\s\S]*?\)|<[0-9A-Fa-f\s]+>)/);
      const dest = body.match(/\/Dest\s*\[\s*(\d+) 0 R/) || body.match(/\/D\s*\[\s*(\d+) 0 R/);
      if (title && dest) {
        const page = pageNumber.get(Number(dest[1]));
        if (page) map.set(decodeTitle(title[1]).trim(), page);
      }
      const first = body.match(/\/First\s+(\d+) 0 R/);
      if (first) walkOutline(Number(first[1]), seen);
      const next = body.match(/\/Next\s+(\d+) 0 R/);
      objectNumber = next ? Number(next[1]) : null;
    }
  };
  const outlinesBody = objects.get(Number(outlinesRef[1])) || "";
  const firstItem = outlinesBody.match(/\/First\s+(\d+) 0 R/);
  if (firstItem) walkOutline(Number(firstItem[1]));
  return map;
}

function usage() {
  console.error("Usage: node render_html_pdf.cjs INPUT.html OUTPUT.pdf [--theme THEME.json] [--client \"Nom du client\"]");
  console.error("Le HTML est imprimé tel quel : aucun style n'est ajouté, la mise en page n'est jamais modifiée.");
  process.exit(2);
}

const input = process.argv[2];
const output = process.argv[3];
if (!input || !output) usage();
if (!fs.existsSync(input)) {
  console.error(`HTML introuvable : ${input}`);
  process.exit(2);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
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

function merge(base, override) {
  const result = { ...base };
  for (const [key, value] of Object.entries(override || {})) {
    result[key] = value && typeof value === "object" && !Array.isArray(value)
      ? merge(base[key] || {}, value)
      : value;
  }
  return result;
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

const clientOptionIndex = process.argv.indexOf("--client");
if (clientOptionIndex >= 0 && !process.argv[clientOptionIndex + 1]) usage();
const clientOverride = clientOptionIndex >= 0 ? process.argv[clientOptionIndex + 1] : null;

const agencyName = String(theme.identity?.agency_name || "RosoAI").trim();
const legalName = String(theme.identity?.legal_name || agencyName).trim();
const methodologyName = String(theme.document?.methodology_name || "SEO/GEO V3").trim();
const methodologyVersion = String(theme.document?.methodology_version || "3.1.0").trim();
const documentDescription = String(theme.document?.description || "Livrable SEO/GEO fondé sur des preuves").trim();
const mutedColor = /^#[0-9a-fA-F]{6}$/.test(String(theme.colors?.muted_text))
  ? String(theme.colors.muted_text)
  : "#7a8499";
const bodyFont = String(theme.typography?.body_family || "Inter").replace(/[^A-Za-z0-9 À-ÿ,'"._-]/g, "");

/**
 * Contrôles de conformité à la charte.
 * `blocking` interdit le rendu ; `warnings` laisse passer en signalant.
 */
function inspectDocument() {
  const blocking = [];
  const warnings = [];

  // Copie du document privée des contenus littéraux : un snippet « prêt à coller »
  // peut légitimement contenir du CSS que la charte interdit dans la mise en page.
  const clone = document.documentElement.cloneNode(true);
  for (const literal of clone.querySelectorAll("pre, code, .snippet")) literal.remove();
  const layoutSource = clone.outerHTML;

  if (!document.documentElement.getAttribute("lang")) {
    blocking.push("attribut lang absent sur <html> : la langue du document est obligatoire.");
  }
  if (!document.title || !document.title.trim()) {
    blocking.push("<title> absent ou vide : le titre du document est obligatoire.");
  }
  if (!document.querySelector("h1")) {
    blocking.push("aucun <h1> : le document doit porter un titre de premier niveau.");
  }

  const imagesWithoutAlt = document.querySelectorAll("img:not([alt])").length;
  if (imagesWithoutAlt > 0) {
    blocking.push(`${imagesWithoutAlt} image(s) sans attribut alt : un texte alternatif est obligatoire (alt="" si décorative).`);
  }

  const viewportUnits = layoutSource.match(/\b\d+(?:\.\d+)?(?:vh|vw|vmin|vmax)\b/g);
  if (viewportUnits) {
    const unique = [...new Set(viewportUnits)].slice(0, 5).join(", ");
    blocking.push(
      `unité viewport interdite dans la mise en page (${unique}) : en impression, 100vh déborde sur une page vide. `
      + "Utiliser des millimètres, par exemple .cover { height: 297mm }."
    );
  }

  const remoteImports = [];
  for (const match of layoutSource.matchAll(/@import\s+(?:url\()?["']?(https?:)?\/\//gi)) remoteImports.push(match[0]);
  for (const link of clone.querySelectorAll('link[rel~="stylesheet"][href]')) {
    if (/^(https?:)?\/\//i.test(link.getAttribute("href"))) remoteImports.push(link.getAttribute("href"));
  }
  for (const match of layoutSource.matchAll(/src:\s*url\(\s*["']?(https?:)?\/\//gi)) remoteImports.push(match[0]);
  if (remoteImports.length) {
    blocking.push(
      `import distant interdit (${remoteImports.length} occurrence(s)) : aucune police ni feuille de style ne doit être `
      + "chargée depuis le réseau. Embarquer les polices dans assets/fonts/ et les déclarer en @font-face local."
    );
  }

  const cover = document.querySelector(".cover");
  if (cover) {
    const style = getComputedStyle(cover);
    const transparent = !style.backgroundColor
      || style.backgroundColor === "transparent"
      || /rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0\s*\)/.test(style.backgroundColor);
    const noImage = !style.backgroundImage || style.backgroundImage === "none";
    if (transparent && noImage) {
      blocking.push(
        "l'élément .cover ne porte aucun fond : le texte de couverture étant blanc, la page serait illisible. "
        + "Chromium n'applique pas background posé sur une règle @page : le fond doit être sur .cover."
      );
    }
    // L'exclusion de l'en-tête sur la couverture repose sur une boîte de marge nulle :
    // les templates y sont clippés. Sans règle @page à marge nulle, la couverture
    // sortirait avec en-tête, pied, marges blanches et page de débordement.
    // La précondition est donc contrôlée par le CSSOM, pas devinée dans le texte source.
    const zeroMarginPages = new Set();
    for (const sheet of document.styleSheets) {
      let rules;
      try {
        rules = sheet.cssRules;
      } catch (error) {
        continue;
      }
      for (const rule of rules) {
        const isPageRule = rule.type === 6 || (rule.constructor && rule.constructor.name === "CSSPageRule");
        if (!isPageRule) continue;
        const margin = String(rule.style?.margin || "").trim();
        if (margin && /^(0(px|mm|pt|cm|in)?)(\s+0(px|mm|pt|cm|in)?)*$/.test(margin)) {
          zeroMarginPages.add(String(rule.selectorText || "").replace(/^@page\s*/i, "").trim());
        }
      }
    }
    const coverPageName = String(getComputedStyle(cover).page || "").trim();
    const coverIsExcluded = zeroMarginPages.has(coverPageName)
      || zeroMarginPages.has(":first")
      || zeroMarginPages.has("");
    if (!coverIsExcluded) {
      blocking.push(
        "la couverture n'est rattachée à aucune page à marge nulle : l'en-tête et le pied s'imprimeraient dessus, "
        + "le fond ne serait pas à fond perdu et la hauteur déborderait sur une page supplémentaire. "
        + "Déclarer @page cover { margin: 0 } et .cover { page: cover }."
      );
    }
  } else {
    warnings.push("aucun élément .cover : le document n'a pas de couverture conforme à la charte.");
  }

  if (!/@font-face/i.test(layoutSource)) {
    warnings.push("aucune police embarquée (@font-face absent) : le rendu dépendra des polices installées sur la machine.");
  }

  const tablesWithoutHead = [...document.querySelectorAll("table")].filter((table) => !table.querySelector("thead")).length;
  if (tablesWithoutHead > 0) {
    warnings.push(`${tablesWithoutHead} tableau(x) sans <thead> : l'en-tête ne sera pas répété en changement de page.`);
  }

  return { blocking, warnings };
}

(async () => {
  const inputPath = path.resolve(input);
  const outputPath = path.resolve(output);
  const bundledAssetRoots = [
    path.resolve(__dirname, "../assets"),
    path.resolve(__dirname, "../skill/roso-seo-geo-v3/assets"),
  ].filter((candidate) => fs.existsSync(candidate));
  const allowedFileRoots = [path.dirname(inputPath), ...bundledAssetRoots];
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const configuredBrowser = process.env.ROSO_CHROME_PATH;
  if (configuredBrowser && !fs.existsSync(configuredBrowser)) {
    throw new Error(`ROSO_CHROME_PATH pointe vers un fichier absent: ${configuredBrowser}`);
  }
  const macChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const executablePath = configuredBrowser || (fs.existsSync(macChrome) ? macChrome : undefined);
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });

  try {
    const page = await browser.newPage();

    // Le rendu reste hors ligne et ne peut lire que le dossier du rapport et les assets du kit.
    await page.route("**/*", (route) => {
      const url = route.request().url();
      if (url.startsWith("data:") || url.startsWith("about:")) return route.continue();
      if (url.startsWith("file://") && localFileAllowed(url, allowedFileRoots)) return route.continue();
      return route.abort();
    });

    await page.goto(pathToFileURL(inputPath).href, { waitUntil: "load" });
    await page.emulateMedia({ media: "print" });

    const report = await page.evaluate(inspectDocument);

    for (const warning of report.warnings) console.error(`Avertissement : ${warning}`);
    if (report.blocking.length) {
      console.error("Rendu refusé : le HTML ne respecte pas la charte.");
      for (const problem of report.blocking) console.error(`- ${problem}`);
      await browser.close();
      process.exit(1);
    }

    const documentTitle = await page.title();
    const clientName = clientOverride
      || await page.evaluate(() => document.querySelector('meta[name="client"]')?.content?.trim() || "");
    const headerLeft = clientName ? `${clientName} × ${agencyName}` : agencyName;
    const footerLeft = headerLeft;

    const headerStyle = `width:100%;padding:0 70px 30px;color:${mutedColor};font-size:9px;font-weight:600;`
      + `letter-spacing:1.5px;text-transform:uppercase;font-family:${escapeHtml(bodyFont)},Arial,sans-serif;`
      + "display:flex;justify-content:space-between;";
    const footerStyle = `width:100%;padding:18px 70px 0;color:${mutedColor};font-size:9px;`
      + `font-family:${escapeHtml(bodyFont)},Arial,sans-serif;display:flex;justify-content:space-between;`;

    // Les templates sont clippés à la hauteur de la boîte de marge : sur la couverture,
    // dont la page est déclarée à marge nulle, ils sont donc invisibles.
    const headerTemplate = `<div style="width:100%;height:100%;overflow:hidden;display:flex;align-items:flex-end">`
      + `<div style="${headerStyle}"><span>${escapeHtml(headerLeft)}</span>`
      + `<span>${escapeHtml(documentTitle)}</span></div></div>`;
    const footerTemplate = `<div style="width:100%;height:100%;overflow:hidden;display:flex;align-items:flex-start">`
      + `<div style="${footerStyle}"><span>${escapeHtml(footerLeft)}</span>`
      + `<span class="pageNumber"></span></div></div>`;

    // Sommaire : première passe pour relever la pagination réelle, puis injection.
    // L'agent n'écrit jamais les numéros de page à la main.
    const pdfOptions = {
      format: "A4",
      printBackground: true, // non négociable : sans lui la couverture sort blanche sur texte blanc
      preferCSSPageSize: true, // honore @page { size: A4; margin: 60px 70px } de la charte
      displayHeaderFooter: true,
      headerTemplate,
      footerTemplate,
      tagged: true,
      outline: true,
    };

    const hasToc = await page.evaluate(() => document.querySelectorAll("[data-toc-page]").length > 0);
    if (hasToc) {
      const firstPass = await page.pdf(pdfOptions);
      const map = outlinePageMap(firstPass);
      const filled = await page.evaluate((entries) => {
        let count = 0;
        for (const cell of document.querySelectorAll("[data-toc-page]")) {
          const key = cell.getAttribute("data-toc-page").trim();
          if (entries[key]) { cell.textContent = String(entries[key]); count += 1; }
        }
        return count;
      }, Object.fromEntries(map));
      const total = await page.evaluate(() => document.querySelectorAll("[data-toc-page]").length);
      if (filled < total) {
        console.error(
          `Avertissement : ${total - filled} entrée(s) de sommaire sans page trouvée. `
          + "Le texte de data-toc-page doit reprendre exactement un titre du document."
        );
      }
    }

    await page.pdf({ ...pdfOptions, path: outputPath });

    appendPdfMetadata(outputPath, {
      title: documentTitle,
      author: [agencyName, legalName].filter((value, index, all) => value && all.indexOf(value) === index).join(" / "),
      subject: documentDescription,
      keywords: `${methodologyName}; version ${methodologyVersion}`,
      creator: `${agencyName} - ${methodologyName} ${methodologyVersion}`,
      producer: `${agencyName} HTML renderer (Chromium/Playwright)`,
    });
  } finally {
    await browser.close();
  }
  console.log(path.resolve(output));
})().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
