# Charte PDF Roso Squad — Spec graphique et template pour Agent 10

---

## ⚙️ VARIABLES À PERSONNALISER (white-label — produis tes audits sous ta propre marque)

> 🎯 **Pour qui ?** Tout acheteur du kit qui veut livrer les audits **sous sa propre identité** (sa propre agence, son logo, ses couleurs) plutôt que sous « RosoAI ». Renseigne ce bloc une fois, puis applique-le (voir « Personnalisation rapide en 3 étapes » plus bas).

### Identité

| Variable | Valeur par défaut | Ta valeur |
|----------|-------------------|-----------|
| `{{NOM_AGENCE}}` | RosoAI | |
| `{{LOGO}}` | (texte « RosoAI ») | (chemin/URL de ton logo, ou ton nom) |
| `{{NOM_CLIENT}}` | [Nom du client] | |
| `{{DATE}}` | [date de l'audit] | |
| `{{CONTACT}}` | @RosoAI | (email / site / handle) |

### Palette couleurs (9 variables hex)

| Variable | Rôle | Valeur par défaut |
|----------|------|-------------------|
| `{{COULEUR_PRIMAIRE}}` | bleu nuit (fonds cover, titres) | `#0e1f3a` |
| `{{COULEUR_ACCENT}}` | orange (accents, soulignés H1) | `#ed8030` |
| `{{COULEUR_SUCCES}}` | vert (🟢 ce qui va bien) | `#2f9d6a` |
| `{{COULEUR_ALERTE}}` | rouge (🔴 ce qui bloque) | `#d94d4d` |
| `{{COULEUR_LIEN}}` | bleu vif (liens, encadrés) | `#3b6ed3` |
| `{{COULEUR_TEXTE}}` | gris foncé (corps de texte) | `#4a5670` |
| `{{COULEUR_TEXTE_DOUX}}` | gris (légendes, footer) | `#7a8499` |
| `{{COULEUR_FOND_DOUX}}` | gris très clair (fonds de bloc) | `#f8f9fc` |
| `{{COULEUR_BORDURE}}` | gris bordures (tableaux) | `#e3e7ef` |

### Typographie (3 variables)

| Variable | Rôle | Valeur par défaut |
|----------|------|-------------------|
| `{{POLICE_TITRES}}` | titres | Inter |
| `{{POLICE_CORPS}}` | corps de texte | Inter |
| `{{POLICE_CODE}}` | blocs de code / snippets | monospace (Menlo, Consolas) |

### Personnalisation rapide en 3 étapes

1. **Cherche-remplace** : dans le CSS ci-dessous, remplace les valeurs par défaut par les tiennes (les hex de la palette, le nom d'agence, le logo, le contact). Un simple chercher-remplacer suffit.
2. **Régénère** les 2 PDF via l'Agent 10 (markdown → HTML → PDF). Le rendu reprend automatiquement tes couleurs et ton identité.
3. **Valide le contraste (WCAG AA)** : vérifie que ton texte reste lisible sur tes fonds (ratio ≥ 4,5:1 pour le corps, ≥ 3:1 pour les gros titres). Outil gratuit : un vérificateur de contraste en ligne. Si un texte clair passe sur un fond clair, fonce-le.

> En 5 minutes, tu produis des audits 100 % à ta marque, prêts à vendre sous ton nom.

---

**Version : Final 30 mai 2026**

Ce fichier est la **source unique de vérité** pour la mise en page des 2 PDF finaux produits par l'Agent 10. Tu DOIS le suivre à la lettre.

---

## Objectif

L'Agent 10 doit produire **deux PDF distincts à chaque audit complet** :

1. **PDF 1 — Audit / Note Stratégique** : ce que les agents ont trouvé (constats, scores, failles, angles morts, axes structurants, par où commencer)
2. **PDF 2 — Plan d'Implémentation** : tout ce qu'il faut mettre en place concrètement, prêt à copier-coller (HTML, JSON-LD, textes réécrits, emails outreach, posts LinkedIn/Reddit, checklists)

Les deux PDF reprennent **exactement la même charte graphique** mais ont des contenus différents :
- Le PDF 1 explique le **pourquoi** (diagnostic)
- Le PDF 2 explique le **comment** (exécution prête-à-coller)

---

## Charte graphique (à respecter strictement)

### Couleurs (palette officielle)

| Usage | Couleur | Hex |
|---|---|---|
| Fond cover | Bleu nuit | `#0e1f3a` |
| Texte sur fond clair | Quasi-noir | `#0e1f3a` |
| Texte secondaire | Gris foncé | `#4a5670` |
| Texte tertiaire | Gris moyen | `#7a8499` |
| Accent principal | Orange | `#ed8030` |
| Statut "Solide" / Vert positif | Vert | `#2f9d6a` |
| Statut "Critique" / Rouge | Rouge | `#d94d4d` |
| Statut "Moyen" / Orange clair | Orange | `#ed8030` |
| Titres de faille / numéros | Bleu vif | `#3b6ed3` |
| Pastille kicker (`PARTIE XX`) | Fond bleu très clair | `#dde8fb` |
| Bordure boîtes | Gris très clair | `#e3e7ef` |
| Fond ligne tableau alterné | Gris très clair | `#f8f9fc` |
| Fond snippets code | Bleu nuit | `#0e1f3a` (texte `#e8ecf5`) |
| Fond boîte "mot de la fin" | Bleu nuit | `#0e1f3a` (texte blanc) |

### Typographie

- **Police principale** : Inter (fallback : `-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif`)
- **Tailles** :
  - Titre cover : 48 px, bold 800
  - H1 sections : 32 px, bold 800
  - H2 sous-sections : 22 px, bold 700
  - H3 (failles, blocs) : 18 px, bold 700
  - Kicker (`PARTIE XX . NOM`) : 11 px, uppercase, letter-spacing 1.5 px, bold 700
  - Étiquettes badges : 11 px, uppercase, letter-spacing 0.8 px, bold 700
  - Corps de texte : 12 px, line-height 1.6
  - Petits labels et footer : 10 px

### Format

- **Format** : A4 (210 × 297 mm)
- **Marges** : 60 px haut/bas, 70 px gauche/droite
- **Header pages intérieures** : `[NOM CLIENT] × ROSOAI` à gauche, `[TITRE PDF]` à droite (uppercase, letter-spacing 1.5 px, gris)
- **Footer pages intérieures** : `[Nom Client] × RosoAI` à gauche, numéro de page à droite (gris)
- **Cover** : pas de header/footer, fond bleu nuit pleine page

---

## Structure des 2 PDF

### PDF 1 — AUDIT (Note Stratégique)

**Nom de fichier** : `Audit_[NomClient]_Note_Strategique.pdf`

**Structure obligatoire** (7 parties) :

1. **Cover** : titre accrocheur en 2 lignes (verdict en une phrase), accroche 3-4 lignes, bloc "Préparé pour / Site analysé / Date / Par"
2. **Sommaire** : "Ce que tu vas trouver ici" + liste numérotée 01 à 07 avec numéros de page
3. **Partie 01 — En 30 secondes** : verdict + 3 KPI cards (Score global, Score visibilité IA /100, nombre de citations IA) + boîte bleu nuit "Le frein principal" + encart "Tes trois priorités absolues, cette semaine"
4. **Partie 02 — Le constat clé** : titre + 2 colonnes side-by-side ("Ce qui tient déjà la route" avec checks verts, "Ce qui te rend invisible" avec croix rouges) + boîte bleu nuit "Personne ne t'a encore pris ta place"
5. **Partie 03 — Tes scores** : "Où tu en es, dimension par dimension" : liste des 9 dimensions notées /10 avec barres de progression colorées (vert ≥7, orange 5-6, rouge <5) + score visibilité IA /100 en gros + boîte "Note de méthode sur la couverture"
6. **Partie 04 — Les failles à corriger** (LE CŒUR DU DOCUMENT) : 3 KPI cards en haut + chaque faille structurée comme : `Faille N. Titre` en bleu + paragraphe explicatif + boîte gris clair "La preuve. [détail vérifié]" + ligne orange "Ce que tu corriges. [action]". À la fin, tableau "Les failles classées par priorité" (Faille / Où ça se joue / Ce que tu prends / Priorité)
7. **Partie 05 — Les angles morts** : "Ce que je n'ai pas pu vérifier" + tableau (Élément / Pourquoi non vérifié / Comment vérifier en 1 minute) + boîte bleu nuit "Aucune affirmation négative sans double-vérification"
8. **Partie 06 — Les trois axes structurants** : 3 cards numérotées (1 / 2 / 3) avec "Pourquoi. / Concrètement. / Résultat visé à 90 jours." + section "Le plan de contenu pour être cité" sous forme de tableau (Contenu à produire / Intention visée / Priorité P1/P2/P3) + boîte gris clair "La règle d'or pour être cité par les IA"
9. **Partie 07 — Par où commencer** : "Cette semaine · cinq actions" (tableau N° / Action / Effort / Impact) + 2 colonnes "D'ici 30 jours" / "D'ici 90 jours" avec bullets orange · puis boîte bleu nuit "Le mot de la fin" · puis bandeau "KPI n°1 à suivre"

### PDF 2 — PLAN D'IMPLÉMENTATION

**Nom de fichier** : `Plan_Implementation_[NomClient].pdf`

**Structure obligatoire** (4 temps · 13 chantiers minimum) :

1. **Cover** : même style, titre type "De l'audit à l'exécution. Sans rien laisser au flou." + accroche "Pour chaque chantier : le problème en une ligne, ce qu'il faut faire, un exemple concret prêt à coller, et comment vérifier que c'est fait."
2. **Sommaire** : "Les treize chantiers" rangés en 4 temps (Temps 1 / Temps 2 / Temps 3 / Temps 4) avec leurs numéros de page
3. **Temps 1 · Les cinq réparations de la semaine** : chantiers 1 à 5 (correctifs rapides, impact fort)
4. **Temps 2 · Les contenus qui te rendent citable** : chantiers 6 à 9 (créations de contenu type page À propos, comparatifs, articles de blog format citable, pages migration)
5. **Temps 3 · L'autorité externe (30 à 90 jours)** : chantiers 10 à 12 (classements d'agences, Reddit/LinkedIn, collecte d'avis)
6. **Temps 4 · En continu** : chantier 13 (tableau de suivi mensuel) + boîte bleu nuit "Comment te servir de ce document"

**Structure de CHAQUE chantier** (à reproduire à l'identique) :
- Badge numéro `N` en bleu (cercle ou carré) + titre du chantier
- Étiquette orange `LE PROBLÈME` + paragraphe court (le problème en une ligne)
- Étiquette verte `À FAIRE` + paragraphe d'action
- **Bloc-snippet prêt à coller** (le cœur de chaque chantier) : encadré sombre `#0e1f3a` avec :
  - Code HTML / JSON-LD / texte / email / message / post → identifié par une étiquette type `LLMS.TXT — PRÊT À COLLER`, `JSON-LD CORRIGÉ`, `TITLE & META DESCRIPTION (À COLLER DANS LE <HEAD>)`, `BRIEF DE L'ARTICLE`, `EMAIL D'OUTREACH PRÊT À ENVOYER`, `SQUELETTE DE POST LINKEDIN`, etc.
- Étiquette verte `VÉRIFIER` + paragraphe de check (comment confirmer que le chantier est bien exécuté)

**Pour les contenus rédactionnels** : fournir 2 à 3 options (ex : 3 options de H1, 2 options de paragraphe-réponse) pour laisser le choix au client.

---

## Contenus prêts-à-coller obligatoires dans le PDF 2

L'Agent 10 doit produire au minimum ces snippets dans le Plan d'Implémentation (selon les failles trouvées) :

1. **Snippets HTML / balises** : `<title>`, `<meta description>`, balises Open Graph, balises Twitter Card
2. **Données structurées JSON-LD** : Organization, LocalBusiness, FAQPage, Article, Person, AggregateRating (corrigé si nécessaire), BreadcrumbList
3. **Fichier llms.txt complet** : structure Markdown avec sections # Marque / > Description / ## Offres / ## Services / ## Réalisations / ## Migration / ## Contact (URLs canoniques uniquement)
4. **Réécritures de blocs texte** :
   - 2-3 options de H1 (avec mot-clé, sous 65 caractères)
   - Paragraphe-réponse 40 à 60 mots à coller sous le hero
   - Page À propos / Équipe (structure + briefs)
   - Brief d'article comparatif (Title / H1 / Intro citable / Plan H2 / tableau comparatif)
   - Bloc FAQ complet (questions + réponses + schema FAQPage)
5. **Emails outreach** : 1 email par cible de classement, prêt à envoyer (Objet + corps + signature)
6. **Squelettes Reddit / LinkedIn** : structure de premier post Reddit + post LinkedIn type "étude de cas"
7. **Messages collecte d'avis** : message court à coller dans WhatsApp / email pour demander un avis Google / Trustpilot
8. **Tableau de suivi mensuel** : KPI à relever (SEO / Visibilité IA / Autorité), où les relever, cibles 90 j
9. **Liste des 7 à 25 prompts** à retester dans ChatGPT / Perplexity / Gemini pour mesurer l'évolution du Score Visibilité IA

---

## CSS complet prêt à utiliser

Voici le CSS exact à utiliser quand l'utilisateur (ou Claude) génère le PDF via markdown → HTML → weasyprint, ou via tout autre moteur HTML/PDF. Ce CSS reproduit fidèlement la charte graphique Roso SEO Squad.

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

@page {
  size: A4;
  margin: 60px 70px;
  @top-left {
    content: var(--header-left);
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #7a8499;
  }
  @top-right {
    content: var(--header-right);
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #7a8499;
  }
  @bottom-left {
    content: var(--footer-left);
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    color: #7a8499;
  }
  @bottom-right {
    content: counter(page);
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    color: #7a8499;
  }
}

@page cover {
  margin: 0;
  background: #0e1f3a;
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 12px;
  line-height: 1.6;
  color: #0e1f3a;
  margin: 0;
}

.cover {
  page: cover;
  background: #0e1f3a;
  color: white;
  padding: 80px 70px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.cover .logo {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 280px;
}

.cover .kicker {
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 600;
  color: #8ba3cf;
  margin-bottom: 16px;
}

.cover h1 {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.1;
  color: white;
  margin: 0 0 24px 0;
}

.cover .accroche {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  max-width: 500px;
  margin-bottom: 60px;
}

.cover .meta {
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 24px;
  display: flex;
  gap: 60px;
}

.cover .meta .item .label {
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: #8ba3cf;
  margin-bottom: 6px;
}

.cover .meta .item .value {
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.cover .note {
  font-size: 11px;
  font-style: italic;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 32px;
  max-width: 600px;
}

.kicker-pill {
  display: inline-block;
  background: #dde8fb;
  color: #3b6ed3;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: 6px 14px;
  border-radius: 4px;
  margin-bottom: 20px;
}

h1.section {
  font-size: 32px;
  font-weight: 800;
  color: #0e1f3a;
  margin: 0 0 12px 0;
  position: relative;
}

h1.section::after {
  content: '';
  display: block;
  width: 40px;
  height: 3px;
  background: #ed8030;
  margin-top: 8px;
}

.intro {
  font-size: 12px;
  color: #4a5670;
  max-width: 600px;
  margin-bottom: 32px;
}

.kpi-row {
  display: flex;
  gap: 16px;
  margin: 24px 0;
}

.kpi-card {
  flex: 1;
  border: 1px solid #e3e7ef;
  border-radius: 8px;
  padding: 24px 16px;
  text-align: center;
}

.kpi-card .value {
  font-size: 38px;
  font-weight: 800;
  color: #ed8030;
  line-height: 1;
}

.kpi-card .value.red { color: #d94d4d; }
.kpi-card .value.green { color: #2f9d6a; }
.kpi-card .value .unit {
  font-size: 18px;
  color: #7a8499;
  font-weight: 600;
}

.kpi-card .label {
  margin-top: 10px;
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  font-weight: 700;
  color: #4a5670;
}

.callout {
  background: #0e1f3a;
  color: white;
  border-radius: 8px;
  padding: 24px 28px;
  margin: 24px 0;
}

.callout h3 {
  color: white;
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 700;
}

.callout p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  margin: 0;
  line-height: 1.6;
}

.priorites {
  background: #f8f9fc;
  border-radius: 8px;
  padding: 20px 24px;
  margin: 24px 0;
}

.priorites h4 {
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.priorites ol {
  margin: 0;
  padding-left: 20px;
}

.priorites ol li {
  margin-bottom: 8px;
}

.constat-row {
  display: flex;
  gap: 16px;
  margin: 24px 0;
}

.constat-card {
  flex: 1;
  border: 1px solid #e3e7ef;
  border-radius: 8px;
  padding: 20px 22px;
}

.constat-card.solide { background: #f3faf6; }
.constat-card.bloque { background: #fdf6f3; }

.badge {
  display: inline-block;
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.badge.solide { background: #2f9d6a; color: white; }
.badge.bloque { background: #d94d4d; color: white; }
.badge.probleme { background: #fde9d9; color: #9a4c0e; }
.badge.afaire { background: #dff3e7; color: #1f6e44; }
.badge.verifier { background: #dff3e7; color: #1f6e44; }
.badge.snippet { background: #fde9d9; color: #9a4c0e; }

.constat-card h4 {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 10px 0;
}

.constat-card ul { list-style: none; padding: 0; margin: 0; }
.constat-card li {
  padding-left: 22px;
  position: relative;
  margin-bottom: 8px;
  font-size: 11.5px;
}

.constat-card.solide li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #2f9d6a;
  font-weight: 700;
}

.constat-card.bloque li::before {
  content: '✕';
  position: absolute;
  left: 0;
  color: #d94d4d;
  font-weight: 700;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f7;
}

.score-row .label-block {
  width: 38%;
}

.score-row .label-block .title {
  font-weight: 700;
  font-size: 13px;
}

.score-row .label-block .sub {
  font-size: 11px;
  color: #7a8499;
}

.score-row .bar {
  flex: 1;
  height: 8px;
  background: #f0f2f7;
  border-radius: 4px;
  overflow: hidden;
}

.score-row .bar .fill {
  height: 100%;
  border-radius: 4px;
}

.score-row .bar .fill.green { background: #2f9d6a; }
.score-row .bar .fill.orange { background: #ed8030; }
.score-row .bar .fill.red { background: #d94d4d; }

.score-row .value {
  width: 60px;
  text-align: right;
  font-weight: 700;
  font-size: 13px;
}

.faille {
  margin: 28px 0;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f2f7;
}

.faille h3 {
  color: #3b6ed3;
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 10px 0;
}

.faille .preuve {
  background: #f8f9fc;
  border-radius: 6px;
  padding: 14px 18px;
  font-size: 11.5px;
  margin: 12px 0;
}

.faille .preuve strong { font-weight: 700; }

.faille .correction {
  font-size: 12px;
  margin-top: 10px;
}

.faille .correction .label {
  color: #ed8030;
  font-weight: 700;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 24px 0;
  font-size: 11.5px;
}

thead { background: #0e1f3a; }
thead th {
  color: white;
  text-align: left;
  padding: 12px 14px;
  font-weight: 600;
  font-size: 11px;
}

tbody td {
  padding: 11px 14px;
  border-bottom: 1px solid #f0f2f7;
}

tbody tr:nth-child(even) { background: #f8f9fc; }

.priority-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.priority-badge.elevee { background: #fde9d9; color: #9a4c0e; }
.priority-badge.moyenne { background: #fdf3df; color: #846108; }
.priority-badge.faible { background: #e6eef9; color: #2c4a7a; }

.priority-badge.p1 { background: #fde9d9; color: #9a4c0e; }
.priority-badge.p2 { background: #fdf3df; color: #846108; }
.priority-badge.p3 { background: #e6eef9; color: #2c4a7a; }

.axe {
  border: 1px solid #e3e7ef;
  border-radius: 8px;
  padding: 22px 26px;
  margin: 18px 0;
}

.axe .num-badge {
  display: inline-block;
  background: #dde8fb;
  color: #3b6ed3;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 6px;
  font-weight: 700;
  font-size: 14px;
  margin-right: 12px;
  vertical-align: middle;
}

.axe h3 {
  display: inline-block;
  vertical-align: middle;
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.axe p { margin: 10px 0; font-size: 12px; }
.axe p strong { color: #0e1f3a; }

.chantier {
  margin: 32px 0;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f2f7;
}

.chantier-header { margin-bottom: 14px; }

.chantier-num {
  display: inline-block;
  background: #3b6ed3;
  color: white;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 6px;
  font-weight: 700;
  font-size: 14px;
  margin-right: 12px;
  vertical-align: middle;
}

.chantier h2 {
  display: inline-block;
  vertical-align: middle;
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.snippet {
  background: #0e1f3a;
  color: #e8ecf5;
  border-radius: 8px;
  padding: 20px 24px;
  font-family: 'SF Mono', Menlo, Monaco, Consolas, monospace;
  font-size: 10.5px;
  line-height: 1.55;
  margin: 14px 0;
  white-space: pre-wrap;
}

.snippet-label {
  display: inline-block;
  background: #fde9d9;
  color: #9a4c0e;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 4px;
  margin-bottom: 0;
  position: relative;
  top: 8px;
}

/* ============================================================
   COMPOSANTS PÉDAGOGIQUES — pédagogie débutant
   .traffic-light  → feu tricolore du verdict (Partie 01, PDF 1)
   .where-to-paste → "où coller ce code" sous chaque snippet (PDF 2)
   .glossary       → glossaire client-friendly (Partie 08, PDF 1)
   .lost-guide     → page "Quoi faire si tu es perdu" (fin PDF 2)
   ============================================================ */

/* --- Feu tricolore (verdict zéro-jargon, Partie 01 du PDF 1) --- */
.traffic-light {
  display: flex;
  gap: 14px;
  margin: 24px 0;
}

.traffic-light .light {
  flex: 1;
  border: 1px solid #e3e7ef;
  border-radius: 8px;
  padding: 18px 18px;
  background: #f8f9fc;
}

.traffic-light .light .dot {
  font-size: 22px;
  line-height: 1;
  margin-bottom: 8px;
}

.traffic-light .light .head {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.4px;
  margin-bottom: 6px;
}

.traffic-light .light .desc {
  font-size: 11px;
  color: #4a5670;
  line-height: 1.5;
}

.traffic-light .light.green  { background: #f3faf6; border-color: #cdeede; }
.traffic-light .light.green .head  { color: #1f6e44; }
.traffic-light .light.orange { background: #fdf6ef; border-color: #f6dcc3; }
.traffic-light .light.orange .head { color: #9a4c0e; }
.traffic-light .light.red    { background: #fdf3f3; border-color: #f3cccc; }
.traffic-light .light.red .head    { color: #a82f2f; }
.traffic-light .light.goal   { background: #eef3fc; border-color: #cfddf6; }
.traffic-light .light.goal .head   { color: #2c4a7a; }

/* --- "Où coller ce code" : table 4 CMS sous un snippet (PDF 2) --- */
.where-to-paste {
  border: 1px solid #e3e7ef;
  border-radius: 8px;
  padding: 14px 18px;
  margin: 10px 0 18px 0;
  background: #f8f9fc;
}

.where-to-paste .wtp-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #2c4a7a;
  margin-bottom: 10px;
}

.where-to-paste table { margin: 0; font-size: 11px; }
.where-to-paste thead { background: #3b6ed3; }
.where-to-paste thead th { padding: 8px 12px; font-size: 10px; }
.where-to-paste tbody td { padding: 8px 12px; }
.where-to-paste .cms { font-weight: 700; color: #0e1f3a; white-space: nowrap; }

/* --- Glossaire client-friendly (Partie 08, fin PDF 1) --- */
.glossary {
  margin: 20px 0;
}

.glossary .gloss-item {
  border-bottom: 1px solid #f0f2f7;
  padding: 12px 0;
}

.glossary .gloss-term {
  font-weight: 800;
  font-size: 13px;
  color: #3b6ed3;
}

.glossary .gloss-def {
  font-size: 11.5px;
  color: #4a5670;
  line-height: 1.55;
  margin-top: 3px;
}

/* Variante compacte en 2 colonnes pour tenir sur une page */
.glossary.cols {
  column-count: 2;
  column-gap: 28px;
}
.glossary.cols .gloss-item {
  break-inside: avoid;
}

/* --- Page "Quoi faire si tu es perdu" (fin PDF 2) --- */
.lost-guide {
  border: 2px solid #3b6ed3;
  border-radius: 10px;
  padding: 26px 30px;
  margin: 24px 0;
  background: #f7faff;
}

.lost-guide h3 {
  color: #0e1f3a;
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 6px 0;
}

.lost-guide .lost-intro {
  font-size: 12px;
  color: #4a5670;
  margin-bottom: 18px;
}

.lost-guide ol {
  margin: 0;
  padding-left: 0;
  list-style: none;
  counter-reset: lost;
}

.lost-guide ol li {
  position: relative;
  padding-left: 42px;
  margin-bottom: 16px;
  font-size: 12px;
  line-height: 1.55;
  counter-increment: lost;
}

.lost-guide ol li::before {
  content: counter(lost);
  position: absolute;
  left: 0;
  top: 0;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  background: #3b6ed3;
  color: white;
  border-radius: 50%;
  font-weight: 800;
  font-size: 13px;
}

.lost-guide ol li strong { color: #0e1f3a; }

.lost-guide .lost-reassure {
  margin-top: 6px;
  padding: 14px 18px;
  background: #0e1f3a;
  color: white;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.55;
}
```

---

## Composants pédagogiques (mode d'emploi)

Ces 4 composants servent la cible « débutant absolu ». Ils sont **obligatoires** aux emplacements indiqués.

### 1. `.traffic-light` — le feu tricolore du verdict

Placé en **Partie 01 du PDF 1**, juste après le paragraphe verdict (avant ou après les 3 KPI cards). Quatre cases, **zéro mot technique** :

- 🟢 **Ce qui va bien** — ce qui tient déjà la route, en mots simples.
- 🟠 **Ce qui est moyen** — à muscler, sans dramatiser.
- 🔴 **Ce qui bloque** — le vrai frein, dit franchement mais sans jargon.
- 🎯 **Par où commencer** — la toute première chose à faire cette semaine.

Le but : qu'en 5 secondes, même quelqu'un qui ne lit pas le reste comprenne où il en est.

```html
<div class="traffic-light">
  <div class="light green"><div class="dot">🟢</div><div class="head">Ce qui va bien</div><div class="desc">Ton site se charge vite et il est clair. Les bases sont saines.</div></div>
  <div class="light orange"><div class="dot">🟠</div><div class="head">Ce qui est moyen</div><div class="desc">Tu écris du contenu, mais pas encore dans le format que les IA recopient.</div></div>
  <div class="light red"><div class="dot">🔴</div><div class="head">Ce qui bloque</div><div class="desc">Personne ne parle de toi ailleurs sur le web. Les IA ne te trouvent pas.</div></div>
  <div class="light goal"><div class="dot">🎯</div><div class="head">Par où commencer</div><div class="desc">Crée ton fichier llms.txt et récupère 5 avis Google cette semaine.</div></div>
</div>
```

### 2. `.where-to-paste` — « où coller ce code »

Placé sous **chaque snippet technique du PDF 2** (HTML, JSON-LD, llms.txt…). Table à 4 CMS pour que le débutant sache exactement où aller. Adapter la dernière colonne au type de code.

```html
<div class="where-to-paste">
  <div class="wtp-title">Où coller ce code ?</div>
  <table>
    <thead><tr><th>Ton outil</th><th>Le chemin exact à suivre</th></tr></thead>
    <tbody>
      <tr><td class="cms">WordPress</td><td>Extension « Insert Headers and Footers » → zone &lt;head&gt;, ou Divi/Elementor → Code custom</td></tr>
      <tr><td class="cms">Webflow</td><td>Project Settings → Custom Code → Head Code (ou réglages de la page)</td></tr>
      <tr><td class="cms">Wix</td><td>Paramètres → Avancé → Code personnalisé → Ajouter, placer dans &lt;head&gt;</td></tr>
      <tr><td class="cms">Shopify</td><td>Boutique en ligne → Thèmes → Modifier le code → theme.liquid, avant &lt;/head&gt;</td></tr>
    </tbody>
  </table>
</div>
```

Pour un fichier (llms.txt, robots.txt, sitemap.xml) qui ne se colle pas dans le `<head>` mais s'héberge à la racine, remplacer le contenu par les chemins type « racine du domaine » pour chaque CMS.

### 3. `.glossary` — le glossaire de fin (Partie 08 du PDF 1)

Reproduit la **section 13 de `00_REGLES_COMMUNES.md`** en version condensée, à la fin du PDF 1. Obligatoire. Utiliser `.glossary.cols` pour tenir sur 1-2 pages.

```html
<div class="glossary cols">
  <div class="gloss-item"><div class="gloss-term">llms.txt</div><div class="gloss-def">Un petit fichier texte qui résume ton site aux IA, comme une antisèche.</div></div>
  <div class="gloss-item"><div class="gloss-term">sameAs</div><div class="gloss-def">La ligne de code qui dit aux IA quels comptes sociaux sont vraiment à toi.</div></div>
  <!-- … reprendre les termes réellement employés dans CE PDF … -->
</div>
```

### 4. `.lost-guide` — « Quoi faire si tu es perdu » (toute fin du PDF 2)

Dernière page du PDF 2. Pour le client qui referme le doc en se disant « ok mais je fais quoi, là, maintenant ? ». Une mini-méthode jour par jour, ton rassurant.

```html
<div class="lost-guide">
  <h3>Tu te sens perdu ? On fait simple.</h3>
  <p class="lost-intro">Pas besoin de tout faire d'un coup. Voici la version "un pas à la fois". Tu fais une seule chose par jour, et c'est déjà énorme.</p>
  <ol>
    <li><strong>Jour 1 :</strong> tu ouvres le Chantier 1, et tu fais <strong>uniquement</strong> celui-là. Rien d'autre.</li>
    <li><strong>Jour 2 :</strong> tu coches le Chantier 1, tu passes au Chantier 2. Toujours un seul.</li>
    <li><strong>Si un code te fait peur :</strong> tu regardes le tableau « Où coller ce code » juste sous le code. Il te dit exactement où aller selon ton outil.</li>
    <li><strong>Si tu bloques vraiment :</strong> tu passes au chantier suivant et tu reviens plus tard. L'ordre est une aide, pas une prison.</li>
    <li><strong>Une fois par mois :</strong> tu refais le test de visibilité IA (dernier chantier) pour voir si ça monte.</li>
  </ol>
  <div class="lost-reassure">Le seul vrai échec, c'est de ne rien faire. Un chantier par semaine, et dans 90 jours tu ne reconnaîtras plus tes résultats. Tu n'as pas besoin d'être expert : tu as besoin d'avancer, doucement.</div>
</div>
```

---

## Méthode de génération (Agent 10)

1. **Tu RÉCUPÈRES** : Brief Site (Agent 01) + toutes les sorties d'agents (02 à 09 + 09bis)
2. **Tu PRODUIS d'abord** : le contenu Markdown structuré du PDF 1 (Audit) en suivant la structure 7 parties + cover + sommaire
3. **Tu PRODUIS ensuite** : le contenu Markdown structuré du PDF 2 (Plan d'Implémentation) en 4 temps × 13 chantiers minimum, avec tous les snippets prêts à coller
4. **Tu DEMANDES** à l'utilisateur s'il veut que tu génères les 2 PDF directement (si environnement Cowork / accès Python + weasyprint) OU si tu lui fournis simplement le code HTML+CSS prêt à imprimer en PDF dans un navigateur
5. **Tu LIVRES** : 2 PDF nommés `Audit_[NomClient]_Note_Strategique.pdf` et `Plan_Implementation_[NomClient].pdf`

---

## Règles absolues

- Tu ne livres JAMAIS un seul PDF : c'est toujours 2 PDF (Audit + Plan)
- Tu ne mets JAMAIS le diagnostic et l'exécution dans le même PDF : c'est la séparation conceptuelle clé
- Le PDF 2 doit contenir AU MINIMUM 10 snippets prêts-à-coller (HTML, JSON-LD, textes, emails, posts)
- Tu respectes la charte couleur à 100% — aucune liberté créative sur la palette
- Tu marques toute donnée non vérifiée comme "Non vérifié" dans le PDF Audit (Partie 05 "Les angles morts")
- Pour les profils sociaux (LinkedIn etc.) : tu appliques la Règle 6 ter de `00_REGLES_COMMUNES.md` (détection garantie par test URL canonique avant toute conclusion d'absence)
