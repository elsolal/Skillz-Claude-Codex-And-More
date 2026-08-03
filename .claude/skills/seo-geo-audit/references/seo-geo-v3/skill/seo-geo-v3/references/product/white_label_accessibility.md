# White-label et accessibilité des livrables

Objectif : générer des livrables réellement personnalisables, cohérents et utilisables, sans masquer la méthode, les limites ou la provenance des données.

## Sommaire

- [Source de vérité de marque](#source-de-vérité-de-marque)
- [Hiérarchie de personnalisation](#hiérarchie-de-personnalisation)
- [Cible d’accessibilité](#cible-daccessibilité)
- [Règles visuelles](#règles-visuelles)
- [Structure sémantique](#structure-sémantique)
- [Tableaux et scores](#règles-pour-les-tableaux-et-scores)
- [Composants obligatoires](#composants-obligatoires-dun-livrable-v3)
- [Thème technique](#thème-technique)
- [QA HTML](#qa-html)
- [QA PDF](#qa-pdf)
- [QA white-label](#qa-white-label)

## Source de vérité de marque

Utiliser un seul fichier de configuration par tenant. Ne pas coder en dur couleur, logo, police, nom d’offre, coordonnées ou mentions légales dans les templates.

Schéma minimal recommandé :

```yaml
brand:
  tenant_id: client_exemple
  public_name: "Agence Exemple"
  legal_name: "À renseigner"
  logo_primary: "assets/logo-primary.svg"
  logo_alt: "Logo Agence Exemple"
  primary: "#123456"
  secondary: "#456789"
  accent: "#D97706"
  text: "#1A1A1A"
  background: "#FFFFFF"
  font_heading: "Inter"
  font_body: "Inter"
  language: "fr-FR"
  website: "https://example.com"
  contact_email: "contact@example.com"
document:
  confidentiality: "Confidentiel — usage interne"
  methodology_name: "Propulsé par SEO/GEO V3"
  show_powered_by: true
  footer_legal: "À valider"
  date_format: "DD/MM/YYYY"
```

Exigences :

- fournir un texte alternatif du logo ;
- vérifier les licences de polices et d’icônes ;
- prévoir une police de repli ;
- conserver un identifiant de méthode/version même lorsque la marque SEO/GEO Squad est masquée commercialement ;
- ne jamais mélanger les assets ou informations de deux tenants ;
- valider le contraste après application des couleurs client.

## Hiérarchie de personnalisation

1. **Contenu** : faits, preuves, actions et limites propres au client.
2. **Identité** : logo, palette, typographie, coordonnées et mentions.
3. **Produit** : nom de l’offre, niveau de support et appels à l’action.
4. **Méthode** : version du moteur, sources, date du run et couverture — toujours conservées dans les métadonnées.

Le white-label ne doit jamais permettre de supprimer :

- la date et le périmètre de mesure ;
- les sources et niveaux de confiance ;
- les limitations ;
- le caractère expérimental d’une fonctionnalité ;
- les obligations légales ou de confidentialité ;
- l’absence de garantie de résultat.

## Cible d’accessibilité

Viser **WCAG 2.2 niveau AA** pour les livrables HTML et interfaces. Pour les PDF, produire un PDF balisé et vérifier les critères applicables ; viser PDF/UA lorsqu’il est contractuellement demandé et que la chaîne de génération le supporte réellement.

Sources :

- WCAG 2.2 : https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices : https://www.w3.org/WAI/ARIA/apg/
- OpenAI, utilité d’ARIA pour les agents : https://help.openai.com/en/articles/12627856-publishers-and-developers-faq
- Google, sites adaptés aux agents : https://web.dev/articles/ai-agent-site-ux

## Règles visuelles

- Contraste texte normal : au moins 4,5:1 ; grand texte : au moins 3:1.
- Ne jamais encoder priorité, statut ou tendance par la couleur seule ; ajouter texte, icône ou motif.
- Taille de corps confortable et redimensionnable ; éviter le texte converti en image.
- Largeur de ligne et interlignage lisibles ; éviter les tableaux trop denses.
- États focus visibles dans les interfaces.
- Liens descriptifs ; éviter « cliquez ici ».
- Graphiques accompagnés d’un résumé textuel et, lorsque nécessaire, d’un tableau de données.
- Conserver la lisibilité en niveaux de gris et à l’impression.
- Éviter les fonds décoratifs derrière les preuves et chiffres critiques.

## Structure sémantique

Chaque livrable doit comporter :

1. un titre unique ;
2. une langue de document ;
3. une hiérarchie de titres sans saut arbitraire ;
4. une table des matières ou des signets pour les documents longs ;
5. des listes natives, pas des puces simulées ;
6. des en-têtes de tableau identifiables ;
7. un ordre de lecture logique ;
8. des textes alternatifs pertinents ;
9. des liens actifs avec libellés compréhensibles ;
10. des métadonnées : titre, auteur/organisation, sujet, version, date et langue.

## Règles pour les tableaux et scores

- Répéter l’en-tête lors d’un changement de page.
- Donner unité, période, source et état de mesure pour chaque métrique.
- Afficher `N/D` plutôt que `0` lorsque la donnée est absente.
- Expliquer l’échelle avant le score.
- Ne pas fusionner dans un même total les métriques de nature différente.
- Inclure une légende textuelle pour les codes `P0/P1/P2`, confiance et statut.
- Éviter les tableaux dépassant la largeur ; préférer plusieurs tableaux ciblés.

## Composants obligatoires d’un livrable V3

### Couverture

- marque et titre du livrable ;
- site/entité analysé ;
- date du run et version de la méthode ;
- classification de confidentialité.

### Encadré méthodologique

- sources consultées ;
- périmètre URLs/marchés/langues ;
- couverture effective ;
- données manquantes ;
- distinction observé/proxy/non mesuré ;
- aucune garantie de crawl, classement ou citation.

### Constat

- identifiant stable ;
- observation en langage simple ;
- preuves et URLs ;
- impact et confiance ;
- date de validité.

### Action

- propriétaire ;
- effort et risque ;
- dépendances ;
- étapes ;
- critère de réussite ;
- rollback lorsque pertinent.

## Thème technique

### Implémentation fournie

Le package utilise `skill/seo-geo-v3/assets/default_theme.json` comme base. Un thème JSON partiel passé avec `--theme` est fusionné avec cette base, puis validé avant tout rendu :

Depuis la racine du Skill installé, préparer une fois les dépendances verrouillées avec `npm ci && npm run install-browser`. Le Skill embarque aussi `requirements-pdf.txt` pour le fallback ReportLab.

```bash
node tools/render_html_pdf.cjs rapport.html rapport.pdf --theme agence/theme.json --client "Nom du client"
```

Le livrable client est composé en HTML par l'Agent 11 selon `templates/Charte_PDF_SEO_GEO_V3.md`, puis imprimé par ce moteur, qui n'ajoute aucun style et refuse tout document non conforme. Les polices Inter et JetBrains Mono sont embarquées dans `assets/fonts/` sous licence OFL : aucun import distant, aucune police système supposée.

`tools/render_tagged_pdf.cjs` et `tools/render_markdown_pdf.py` sont des **outils de contrôle interne** convertissant du Markdown avec leur propre mise en page. Ils ne suivent pas la charte et ne produisent pas de livrable client.

Les tokens appliqués couvrent l’identité et les coordonnées de l’agence, la langue, un logo PNG/JPEG/SVG local pour Chromium, la palette, les polices avec fallback, le format, l’orientation, les textes de couverture, la confidentialité, la description, l’en-tête, le pied de page et la pagination. Les formats de date, devise et unités sont aussi embarqués comme métadonnées de thème pour les templates en amont. Le logo reste borné à 2 Mio et à l’intérieur du dossier du thème. Le renderer balisé échappe le HTML brut, applique une CSP et bloque toute requête réseau pendant le rendu. ReportLab accepte PNG/JPEG et constitue un fallback non balisé.

Les flags `layout.show_header`, `layout.show_footer` et `layout.show_page_numbers` sont réellement appliqués. Le nom de méthode et sa version restent obligatoires : une personnalisation commerciale ne peut pas rendre la provenance méthodologique anonyme.

Le fichier réellement livré est JSON afin d’être lu sans dépendance supplémentaire. Le YAML ci-dessous reste un modèle conceptuel pour un futur portail ou une configuration de tenant plus large.

Utiliser des variables, jamais des hexadécimales dispersées :

```css
:root {
  --brand-primary: #123456;
  --brand-secondary: #456789;
  --brand-accent: #D97706;
  --text-primary: #1A1A1A;
  --surface: #FFFFFF;
  --status-critical: #B42318;
  --status-warning: #8A4B00;
  --status-success: #146C43;
}
```

Prévoir une validation automatisée des tokens : format couleur, contraste, fichiers présents, texte alternatif, police autorisée et longueur des mentions.

## QA HTML

- [ ] Attribut `lang` correct.
- [ ] Un seul `h1`, titres ordonnés selon la structure logique.
- [ ] Navigation clavier complète et focus visible.
- [ ] Formulaires avec labels, erreurs et instructions accessibles.
- [ ] Images avec alt utile ou alt vide si décoratives.
- [ ] Graphiques décrits textuellement.
- [ ] Contraste vérifié sur tous les états.
- [ ] Aucune information transmise par couleur seule.
- [ ] Liens et boutons ont un nom accessible clair.
- [ ] Impression et affichage mobile testés.

## QA PDF

- [ ] PDF non scanné ; texte sélectionnable.
- [ ] PDF balisé avec ordre de lecture logique.
- [ ] Titre du document défini et langue correcte.
- [ ] Titres, listes, tableaux et figures balisés.
- [ ] Textes alternatifs définis.
- [ ] Signets présents pour les documents longs.
- [ ] Liens testés.
- [ ] Aucune coupure de texte, ligne orpheline critique ou tableau illisible.
- [ ] Contraste et niveaux de gris vérifiés.
- [ ] Pieds de page, pagination et confidentialité cohérents.
- [ ] Validation par rendu de toutes les pages, pas seulement la première.

## QA white-label

- [ ] Aucun ancien nom de client ou chemin local résiduel.
- [ ] Logo, couleurs, polices et coordonnées proviennent de la configuration active.
- [ ] Mentions légales validées.
- [ ] Assets sous licence.
- [ ] Version de méthode et date visibles dans les métadonnées.
- [ ] Les exemples sont fictifs ou autorisés.
- [ ] Aucun secret ou identifiant interne dans le PDF/HTML.
- [ ] Le contraste reste conforme avec la palette client.
- [ ] Une version accessible du contenu est fournie lorsque le format principal ne suffit pas.
