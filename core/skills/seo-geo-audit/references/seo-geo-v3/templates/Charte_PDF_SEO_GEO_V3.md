# Charte PDF SEO/GEO V3

**Bloc d'adaptation V2 → V3 — version 3.1.0**

> ⚠️ **Ce bloc prime sur le corps du document en cas de divergence.**
>
> Tout ce qui suit le séparateur « DÉBUT DE LA CHARTE V2 » est l'ancienne charte V2, copiée **verbatim** pour sa structure et son CSS. Le bloc d'adaptation V3 ci-dessous impose toutefois une identité neutre et prime sur tous les exemples historiques de marque.
>
> Les huit sections ci-dessous adaptent cette charte au moteur et aux données de la V3. Lorsqu'une consigne du corps V2 contredit une consigne de ce bloc, **c'est ce bloc qui s'applique**.

---

## 1. C'est l'Agent 11 qui compose le livrable

Le livrable client n'est plus produit par un script. `core/agents/11_Master_Final_Report_V3.md` **rédige et compose lui-même le HTML complet** des deux documents, en suivant cette charte, exactement comme l'Agent 10 le faisait en V2.

`skill/seo-geo-v3/scripts/generate_markdown_reports.py` n'est plus le producteur du PDF client. Il devient un **outil de contrôle interne** : il sert à vérifier que les registres sont complets et cohérents, jamais à fabriquer le document remis au client.

## 2. Chaîne de rendu

```text
Agent 11 → HTML complet (charte appliquée) → moteur d'impression → PDF A4 balisé
```

L'agent écrit le HTML ; le moteur `skill/seo-geo-v3/tools/render_html_pdf.cjs` l'imprime **sans jamais modifier la mise en page**. Le moteur n'ajoute aucun style, ne reformate rien, n'injecte aucune CSS de son cru : il imprime ce que l'agent a composé, en A4 balisé, avec sommaire et métadonnées.

L'ancien moteur `render_tagged_pdf.cjs` prend du markdown et impose sa propre feuille de style : il écraserait cette charte. Il ne doit **plus** être utilisé pour un livrable client.

## 3. Toute donnée vient des objets structurés validés

L'agent puise exclusivement dans : `findings.json`, `actions.json`, `evidence.jsonl`, `facts.json`, `geo_runs/*.json` et le score canonique `reports/score_v3.json`.

Il **reformule, vulgarise et hiérarchise** ; il n'invente **aucun chiffre, aucun constat, aucune preuve, aucun concurrent**. Un chiffre absent des registres ne peut pas apparaître dans le document. La liberté rédactionnelle porte sur la formulation et l'ordre, jamais sur les faits.

## 4. Les scores : 5 dimensions V3, jamais de note globale

La partie « scores » de la V2 (9 dimensions notées /10 + score global) est **remplacée** par les cinq dimensions canoniques V3 :

| Dimension | Libellé à afficher |
|---|---|
| `F_foundations` | **F — Fondations** |
| `V_ai_visibility` | **V — Visibilité IA** |
| `O_opportunity` | **O — Opportunité** |
| `E_execution` | **E — Exécution** |
| `M_measurement` | **M — Mesure** |

- La **barre de progression** de la charte V2 (`.score-row`, `.bar`, `.fill`) est **conservée** telle quelle, code couleur compris.
- Sous chaque barre, afficher la **couverture** et la **confiance** de la dimension.
- **Interdiction absolue** d'afficher une moyenne, un score global unique, une note agrégée ou un « score sur 100 » toutes dimensions confondues. Les blocs `.kpi-card` « Score global » de la charte V2 sont supprimés au profit de KPI qui ne mélangent pas les dimensions.

## 5. Traitement du non-mesuré

- **Jamais de barre à zéro** pour une dimension non mesurée : une barre vide se lit comme un mauvais score, ce qui serait un mensonge visuel.
- **Jamais de tableau dont toutes les lignes seraient « Non mesuré »** : un tel tableau n'apporte rien et casse la lecture.
- À la place, écrire **une phrase en clair** qui dit ce qui n'a pas été mesuré et pourquoi, puis **renvoyer explicitement vers la partie « Les angles morts »**.

Exemple attendu :

> La visibilité dans les réponses IA n'a pas été mesurée sur cet audit : aucun run GEO n'a été réalisé. Voir la partie 05, « Les angles morts », pour la marche à suivre.

## 6. Preuves : registre en annexe, preuve lisible dans le corps

- Le **registre brut des preuves** (identifiants `ev_...`, statuts, dates) passe en **annexe de fin de document**. Il ne coupe plus la lecture.
- Dans le corps, chaque faille cite sa preuve **en français lisible**, au format V2 :

> **La preuve.** Test direct de `exemple.fr/llms.txt` : réponse 404, double-vérifié.

- Un identifiant technique (`ev_`, `finding_`, `action_`) ne doit **jamais** apparaître dans le corps du document client. Il reste disponible en annexe pour la traçabilité.

## 7. Header, footer et pagination sous Chromium

Le moteur d'impression est **Chromium**, retenu pour le PDF balisé et le sommaire cliquable, acquis de la V3 à préserver. Conséquences sur la charte V2 :

- Les boîtes de marge `@page { @top-left / @top-right / @bottom-left / @bottom-right }` du CSS V2 **ne sont pas appliquées par Chromium**. Elles sont remplacées par les `headerTemplate` et `footerTemplate` du moteur.
- **Le contenu reste strictement celui de la charte V2** : en en-tête, `[NOM CLIENT] × [AGENCE]` à gauche et le **titre du PDF** à droite, en **uppercase gris avec letter-spacing** ; en pied, `[Nom Client] × [Agence]` à gauche et le **numéro de page** à droite.
- **La couverture n'a ni header ni footer.** La première page est exclue des deux templates.
- `@page { size: A4; margin: 60px 70px }` est **conservé et honoré** via `preferCSSPageSize`. Ces marges réservent la place des templates : elles ne doivent pas être réduites.

Le fond bleu nuit de la couverture doit être porté par l'élément `.cover` lui-même : Chromium n'applique pas `background` posé sur une règle `@page`.

### Hauteur de la couverture : `297mm`, jamais `vh`

Le corps V2 déclare `.cover { height: 100vh }` (ligne unique du CSS à utiliser une unité viewport). **Cette règle est remplacée.**

Sous Chromium, `100vh` vaut la hauteur du **viewport**, supérieure à la hauteur imprimable A4 : la couverture déborde alors sur une deuxième page entièrement bleu nuit et vide. Vérifié au rendu.

```css
html, body { height: 100%; }
.cover { height: 100%; }    /* jamais 100vh, et pas 297mm non plus */
```

**Ne pas utiliser `height: 297mm` non plus.** Vérifié au rendu : sur un document court la valeur en millimètres remplit correctement la page, mais sur un document long le fond de couverture ne descend qu'aux trois quarts de la hauteur et laisse une bande blanche en bas. Seul `height: 100%`, adossé à `html, body { height: 100% }`, donne un fond à fond perdu fiable quelle que soit la longueur du document.

Aucune unité viewport (`vh`, `vw`, `vmin`, `vmax`) ne doit apparaître dans le HTML généré. Le `height: 100%` du remplissage de barre (`.score-row .bar .fill`) n'est pas concerné : il se calcule dans un parent de hauteur fixe.

### Fonds imprimés : `printBackground` obligatoire

Le moteur imprime **toujours** avec `printBackground: true`, en dur, **sans option pour le désactiver**. Sans ce réglage, la couverture sort blanche avec du texte blanc — donc illisible — et tous les fonds bleu nuit, en-têtes de tableau, badges et encadrés disparaissent. Vérifié au rendu.

Le moteur **refuse de rendre** si l'élément `.cover` ne porte pas de fond : le texte de couverture étant blanc, un fond absent produirait une page illisible.

## 8. Aucun import distant dans le HTML final

La ligne `@import url('https://fonts.googleapis.com/...')` du CSS V2 est **neutralisée**. Elle reste présente verbatim dans le corps ci-dessous, mais **ne doit pas être reprise** dans le HTML généré.

**Aucun import distant, aucune requête réseau, aucune police hébergée** ne doit subsister dans le HTML final : ni `@import`, ni `<link rel="stylesheet">`, ni `<script src>`, ni image en URL distante. Inter est **embarquée localement** dans `skill/seo-geo-v3/assets/fonts/` et déclarée par des règles `@font-face` en base64 ou en chemin local. Le document doit se rendre à l'identique sur une machine hors ligne.

## 9. Aucune dépendance à une police système

Un livrable client ne peut pas dégrader selon la machine de l'acheteur. Deux dépendances du CSS V2 sont donc neutralisées.

### Le feu tricolore : pastilles CSS, plus d'emoji

Le corps V2 construit `.traffic-light` avec quatre emoji (`🟢 🟠 🔴 🎯`) dans `.dot`. Les emoji dépendent d'une police emoji couleur installée sur la machine : sans elle, ils tombent en carrés noirs. `.traffic-light` étant un composant signature, cette dégradation est inacceptable.

Les quatre emoji sont **remplacés par des pastilles CSS colorées accompagnées d'un libellé texte** :

```html
<div class="light green">
  <div class="dot" aria-hidden="true"></div>
  <div class="head">Ce qui va bien</div>
  <div class="desc">…</div>
</div>
```

```css
.traffic-light .light .dot {
  width: 14px; height: 14px; border-radius: 50%;
  margin-bottom: 8px; display: block;
}
.traffic-light .light.green  .dot { background: #2f9d6a; }
.traffic-light .light.orange .dot { background: #ed8030; }
.traffic-light .light.red    .dot { background: #d94d4d; }
.traffic-light .light.goal   .dot { background: #3b6ed3; }
```

Le sens n'est **jamais** porté par la couleur seule : le libellé texte (`Ce qui va bien`, `Ce qui est moyen`, `Ce qui bloque`, `Par où commencer`) reste obligatoire à côté de chaque pastille. Cela satisfait au passage la règle d'accessibilité « jamais la couleur seule » de `references/product/white_label_accessibility.md`.

### Les snippets : monospace embarquée

Le corps V2 déclare `.snippet { font-family: 'SF Mono', Menlo, Monaco, Consolas, monospace }` : ce sont des polices macOS et Windows, absentes ailleurs. Une **monospace libre est embarquée localement** dans `skill/seo-geo-v3/assets/fonts/`, au même titre qu'Inter, et déclarée par `@font-face`. Les snippets doivent avoir des chasses identiques sur toute machine.

De même, la pile `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto` du corps V2 devient sans effet une fois Inter embarquée : elle ne sert plus que de repli ultime.

### Les fichiers livrés et la règle à copier

| Famille | Rôle | Licence |
|---|---|---|
| **Inter** | Titres et corps | OFL 1.1 |
| **JetBrains Mono** | Snippets et code | OFL 1.1 |

Les deux sont **variables** : un seul fichier par sous-ensemble couvre les graisses 400, 500, 600, 700 et 800.

`skill/seo-geo-v3/assets/fonts/fonts.css` contient les quatre règles `@font-face` **déjà encodées en base64**. Copier son contenu en tête du `<style>` du document, puis déclarer :

```css
body     { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.snippet { font-family: 'JetBrains Mono', Menlo, Monaco, Consolas, monospace; }
```

Ne jamais référencer les `.woff2` par un chemin relatif : le HTML du livrable est écrit dans le dossier projet du client, hors du kit, où ce chemin serait cassé. Le base64 rend le document autonome.

## 10. Le mode « estimation ancrée »

Un audit sans accès aux moteurs IA ni à la Search Console reste un **audit de premier rang**, pas une version dégradée. La V2 traitait ce cas par un mode déclaré ; la V3 le reprend sous le nom `estimation_ancree`.

### Trois états, jamais deux

Le document distingue **trois** états, et ne confond jamais les deux derniers :

| État | Ce que c'est | Comment il s'affiche |
|---|---|---|
| **Mesuré** | Relevé par test direct ou export de première partie | Valeur exacte, barre pleine |
| **Estimé** | Déduit de recherches web réelles et concordantes | **Intervalle** + mention « estimé » visible |
| **Non mesuré** | Ni testé ni estimable | Phrase en clair, renvoi vers les Angles morts |

Faire tomber en « non mesuré » tout ce qui n'est pas mesuré vide le rapport de sa substance. C'est précisément ce que ce mode corrige.

### Les cinq règles du mode, non négociables

1. **Trois sources concordantes minimum par affirmation.** Une estimation s'appuie exclusivement sur des recherches web réelles. Chaque source est tracée dans `evidence.jsonl` avec son URL, sa date de consultation et son extrait. Deux sources ne suffisent pas.
2. **Jamais de chiffre unique.** Toute valeur estimée est publiée sous forme d'**intervalle** et porte visuellement la mention « estimé ». Écrire « entre 45 et 69 » et non « 57 ».
3. **Le mode est annoncé en couverture** — dans la note de bas de couverture — **et détaillé dans une boîte « Note de méthode sur la couverture »** en partie 03, comme en V2.
4. **Aucune affirmation négative sur le site audité ne peut reposer sur une estimation.** Dire « ton llms.txt est absent », « tu n'as pas de page bio », « tu n'es pas cité » exige un **test direct double-vérifié**. Une estimation ne prouve jamais une absence.
5. **La partie 05 liste chaque point estimé** avec la manière de le confirmer en test direct, ligne par ligne.

### Rendu visuel de l'estimation

L'intervalle utilise la barre de la charte, avec une zone grisée pour la plage et la mention à droite :

```html
<div class="score-row">
  <div class="label-block"><div class="title">V — Visibilité IA</div>
    <div class="sub">Estimation ancrée sur 3 sources</div></div>
  <div class="bar"><div class="fill estimated" style="margin-left:45%; width:24%"></div></div>
  <div class="value">45–69 <span class="est-tag">estimé</span></div>
</div>
```

```css
.score-row .bar .fill.estimated { background: repeating-linear-gradient(45deg,#8ba3cf,#8ba3cf 4px,#c9d5ea 4px,#c9d5ea 8px); }
.est-tag { display:inline-block; font-size:9px; font-weight:700; letter-spacing:.5px; text-transform:uppercase;
           color:#2c4a7a; background:#e6eef9; border-radius:3px; padding:2px 6px; margin-left:6px; }
```

La trame diagonale distingue l'estimation d'une mesure au premier coup d'œil, et la mention texte assure que le sens n'est jamais porté par le seul motif.

## 11. Pas de quota de chantiers ni de snippets

Le corps V2 impose « 13 chantiers minimum » et « au minimum 10 snippets prêts-à-coller ». **Ces deux quotas sont supprimés.**

Règle de remplacement : **un chantier par action validée dans `actions.json`, ni plus ni moins**. Un snippet est fourni **lorsque l'action porte sur du code, un fichier ou un texte à coller** — pas pour atteindre un nombre.

**Interdiction explicite** de créer un chantier, une action ou un snippet dans le but d'atteindre un total. Un quota pousse à fabriquer ; c'est contraire à tout le reste du kit. Un plan de trois chantiers réels vaut mieux qu'un plan de treize dont dix sont inventés.

## 12. Les numéros du sommaire sont calculés, jamais écrits

L'agent n'écrit jamais un numéro de page à la main. Il place un marqueur dans le sommaire :

```html
<div class="toc-row"><span class="n">01</span>
  <span class="t">En 30 secondes — le verdict</span>
  <span class="p" data-toc-page="Le verdict, sans détour"></span></div>
```

La valeur de `data-toc-page` reprend **exactement** le titre `<h1>` de la partie visée. Le moteur `render_html_pdf.cjs` effectue une première passe de rendu, relève la pagination réelle dans les signets du PDF, injecte les numéros, puis produit la version finale. Il avertit si une entrée du sommaire ne trouve pas sa page.

---

# DÉBUT DE LA CHARTE V2 — COPIE VERBATIM

*Le texte ci-dessous reprend la structure de la charte SEO/GEO V2. Les divergences avec la V3 et les règles de neutralité sont traitées par le bloc d'adaptation ci-dessus, qui prime.*

---

# Charte PDF SEO/GEO Squad — Spec graphique et template pour Agent 10

---

## ⚙️ VARIABLES À PERSONNALISER (white-label — produis tes audits sous ta propre marque)

> 🎯 **Pour qui ?** Tout acheteur du kit qui veut livrer les audits **sous sa propre identité** (sa propre agence, son logo, ses couleurs) plutôt que sous « SEO/GEO Squad ». Renseigne ce bloc une fois, puis applique-le (voir « Personnalisation rapide en 3 étapes » plus bas).

### Identité

| Variable | Valeur par défaut | Ta valeur |
|----------|-------------------|-----------|
| `{{NOM_AGENCE}}` | SEO/GEO Squad | |
| `{{LOGO}}` | (texte « SEO/GEO Squad ») | (chemin/URL de ton logo, ou ton nom) |
| `{{NOM_CLIENT}}` | [Nom du client] | |
| `{{DATE}}` | [date de l'audit] | |
| `{{CONTACT}}` | À personnaliser | (email / site / handle) |

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

**Version : v2.2 — juin 2026**

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
- **Header pages intérieures** : `[NOM CLIENT] × [IDENTITÉ APPROUVÉE]` à gauche, `[TITRE PDF]` à droite (uppercase, letter-spacing 1.5 px, gris)
- **Footer pages intérieures** : `[Nom Client] × SEO/GEO Squad` à gauche, numéro de page à droite (gris)
- **Cover** : pas de header/footer, fond bleu nuit pleine page

---

## Structure des 2 PDF

### PDF 1 — AUDIT (Note Stratégique)

**Nom de fichier** : `Audit_[NomClient]_Note_Strategique.pdf`

**Structure obligatoire** (8 parties) :

1. **Cover** : titre accrocheur en 2 lignes (verdict en une phrase), accroche 3-4 lignes, bloc "Préparé pour / Site analysé / Date / Par"
2. **Sommaire** : "Ce que tu vas trouver ici" + liste numérotée 01 à 08 avec numéros de page
3. **Partie 01 — En 30 secondes** : verdict + 3 KPI cards (Score global, Score visibilité IA /100, nombre de citations IA) + boîte bleu nuit "Le frein principal" + encart "Tes trois priorités absolues, cette semaine"
4. **Partie 02 — Le constat clé** : titre + 2 colonnes side-by-side ("Ce qui tient déjà la route" avec checks verts, "Ce qui te rend invisible" avec croix rouges) + boîte bleu nuit "Personne ne t'a encore pris ta place"
5. **Partie 03 — Tes scores** : "Où tu en es, dimension par dimension" : liste des 9 dimensions notées /10 avec barres de progression colorées (vert ≥7, orange 5-6, rouge <5) + score visibilité IA /100 en gros + **part de voix IA** (composant `.share-voice`, toi vs concurrents réellement cités) + ligne tonalité + boîte "Note de méthode sur la couverture"
6. **Partie 04 — Les failles à corriger** (LE CŒUR DU DOCUMENT) : 3 KPI cards en haut + chaque faille structurée comme : `Faille N. Titre` en bleu + paragraphe explicatif + boîte gris clair "La preuve. [détail vérifié]" + ligne orange "Ce que tu corriges. [action]". À la fin, tableau "Les failles classées par priorité" (Faille / Où ça se joue / Ce que tu prends / Priorité)
7. **Partie 05 — Les angles morts** : "Ce que je n'ai pas pu vérifier" + tableau (Élément / Pourquoi non vérifié / Comment vérifier en 1 minute) + boîte bleu nuit "Aucune affirmation négative sans double-vérification"
8. **Partie 06 — Les trois axes structurants** : 3 cards numérotées (1 / 2 / 3) avec "Pourquoi. / Concrètement. / Résultat visé à 90 jours." + section "Le plan de contenu pour être cité" sous forme de tableau (Contenu à produire / Intention visée / Priorité P1/P2/P3) + boîte gris clair "La règle d'or pour être cité par les IA"
9. **Partie 07 — Par où commencer** : "Cette semaine · cinq actions" (tableau N° / Action / Effort / Impact) + 2 colonnes "D'ici 30 jours" / "D'ici 90 jours" avec bullets orange · puis boîte bleu nuit "Le mot de la fin" · puis bandeau "KPI n°1 à suivre"
10. **Partie 08 — Le glossaire** (OBLIGATOIRE, dernière partie) : "Les mots techniques, en français normal" — composant `.glossary.cols` en 2 colonnes, uniquement les termes réellement employés dans ce PDF, définitions reprises de la section 13 de `00_REGLES_COMMUNES.md`

### PDF 2 — PLAN D'IMPLÉMENTATION

**Nom de fichier** : `Plan_Implementation_[NomClient].pdf`

**Structure obligatoire** (4 temps · 13 chantiers minimum) :

1. **Cover** : même style, titre type "De l'audit à l'exécution. Sans rien laisser au flou." + accroche "Pour chaque chantier : le problème en une ligne, ce qu'il faut faire, un exemple concret prêt à coller, et comment vérifier que c'est fait."
2. **Sommaire** : "Les treize chantiers" rangés en 4 temps (Temps 1 / Temps 2 / Temps 3 / Temps 4) avec leurs numéros de page
3. **Temps 1 · Les cinq réparations de la semaine** : chantiers 1 à 5 (correctifs rapides, impact fort)
4. **Temps 2 · Les contenus qui te rendent citable** : chantiers 6 à 9 (créations de contenu type page À propos, comparatifs, articles de blog format citable, pages migration)
5. **Temps 3 · L'autorité externe (30 à 90 jours)** : chantiers 10 à 12 (classements d'agences, Reddit/LinkedIn, collecte d'avis)
6. **Temps 4 · En continu** : chantier 13 (tableau de suivi mensuel) + boîte bleu nuit "Comment te servir de ce document"
7. **Page finale — « Quoi faire si tu es perdu »** (OBLIGATOIRE, toute dernière page) : composant `.lost-guide`, méthode « un chantier à la fois », zéro jargon, encadré rassurant `.lost-reassure`

**Structure de CHAQUE chantier** (à reproduire à l'identique) :
- Badge numéro `N` en bleu (cercle ou carré) + titre du chantier
- Étiquette orange `LE PROBLÈME` + paragraphe court (le problème en une ligne)
- Étiquette verte `À FAIRE` + paragraphe d'action
- **Bloc-snippet prêt à coller** (le cœur de chaque chantier) : encadré sombre `#0e1f3a` avec :
  - Code HTML / JSON-LD / texte / email / message / post → identifié par une étiquette type `LLMS.TXT — PRÊT À COLLER`, `JSON-LD CORRIGÉ`, `TITLE & META DESCRIPTION (À COLLER DANS LE <HEAD>)`, `BRIEF DE L'ARTICLE`, `EMAIL D'OUTREACH PRÊT À ENVOYER`, `SQUELETTE DE POST LINKEDIN`, etc.
- **Bloc `OÙ COLLER CE CODE`** (composant `.where-to-paste`, OBLIGATOIRE dès que le snippet est du code à insérer dans le site) : tableau 4 CMS (WordPress / Webflow / Wix / Shopify) avec le chemin exact
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

Voici le CSS exact à utiliser quand l'utilisateur (ou Claude) génère le PDF via markdown → HTML → weasyprint, ou via tout autre moteur HTML/PDF. Ce CSS reproduit fidèlement la charte graphique SEO/GEO Squad.

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

/* Part de voix IA (NOUVEAU v2.1) — barre empilée toi vs concurrents, Partie 03 du PDF 1 */
.share-voice { margin: 18px 0 4px; }
.share-voice .sv-title { font-weight: 700; font-size: 13px; color: #0e1f3a; margin-bottom: 8px; }
.share-voice .sv-bar {
  display: flex; width: 100%; height: 26px;
  border-radius: 6px; overflow: hidden;
  font-size: 10px; font-weight: 700; color: #ffffff;
}
.share-voice .sv-seg { display: flex; align-items: center; justify-content: center; white-space: nowrap; overflow: hidden; }
.share-voice .sv-seg.brand { background: #0e1f3a; }
.share-voice .sv-seg.c1 { background: #5e6b85; }
.share-voice .sv-seg.c2 { background: #8c95ab; }
.share-voice .sv-seg.c3 { background: #b6bdcd; color: #0e1f3a; }
.share-voice .sv-seg.cx { background: #d2d8e4; color: #0e1f3a; }
.share-voice .sv-legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 8px; font-size: 10px; color: #4a5670; }
.share-voice .sv-legend .item { display: flex; align-items: center; gap: 5px; }
.share-voice .sv-legend .chip { width: 10px; height: 10px; border-radius: 2px; }
.tonalite-line { margin: 8px 0 4px; font-size: 12px; color: #4a5670; }
.tonalite-line strong { color: #0e1f3a; }

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

Ces 5 composants servent la cible « débutant absolu ». Les quatre premiers sont **obligatoires** aux emplacements indiqués ; le cinquième (part de voix) est obligatoire **dès que** l'Agent 09bis a produit une part de voix (Bloc 2 bis).

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

### 5. `.share-voice` — la part de voix IA (Partie 03 du PDF 1, NOUVEAU v2.1)

Placée **juste sous le score de Visibilité IA** en Partie 03. Une barre empilée qui montre, en un coup d'œil, quelle part des citations IA ta marque capte vs tes concurrents — sur les réponses **réellement testées** par l'Agent 09bis (Bloc 2 bis). Le segment bleu nuit, c'est toi. Suivie d'une ligne de tonalité. Obligatoire dès qu'une part de voix existe ; si l'audit était en estimation seule, ajouter « part de voix estimée, à confirmer ». Largeur de chaque segment = sa part de voix en %.

```html
<div class="share-voice">
  <div class="sv-title">Ta part de voix face aux IA</div>
  <div class="sv-bar">
    <div class="sv-seg brand" style="width:24%">Toi 24%</div>
    <div class="sv-seg c1" style="width:37%">Concurrent A 37%</div>
    <div class="sv-seg c2" style="width:21%">Concurrent B 21%</div>
    <div class="sv-seg c3" style="width:18%">Concurrent C 18%</div>
  </div>
  <div class="sv-legend">
    <span class="item"><span class="chip" style="background:#0e1f3a"></span>Toi</span>
    <span class="item"><span class="chip" style="background:#5e6b85"></span>Concurrent A</span>
    <span class="item"><span class="chip" style="background:#8c95ab"></span>Concurrent B</span>
    <span class="item"><span class="chip" style="background:#b6bdcd"></span>Concurrent C</span>
  </div>
</div>
<p class="tonalite-line"><strong>Quand tu es cité, le ton est :</strong> majoritairement neutre-factuel (sur 9 citations réelles). Source : tests réels de l'Agent 09bis.</p>
```

Règle : ce composant n'affiche QUE des acteurs réellement cités par une IA (jamais un concurrent ajouté « pour faire joli »). Si la marque n'est citée nulle part en réel, on l'écrit honnêtement (« marque pas encore citée dans les tests réels ») au lieu d'inventer une part de voix.

---

## Méthode de génération (Agent 10)

1. **Tu RÉCUPÈRES** : Brief Site (Agent 01) + toutes les sorties d'agents (02 à 09 + 09bis)
2. **Tu PRODUIS d'abord** : le contenu Markdown structuré du PDF 1 (Audit) en suivant la structure 8 parties (glossaire inclus) + cover + sommaire
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
