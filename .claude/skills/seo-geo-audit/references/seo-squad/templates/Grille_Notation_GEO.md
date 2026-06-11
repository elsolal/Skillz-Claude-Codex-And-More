# Grille de Notation GEO — Roso SEO Squad

> Ce template est utilisé par l'Agent 09 (Visibilité IA & Plan d'Action). Il sert à noter la présence de la marque dans les réponses des IA conversationnelles de façon structurée, reproductible et honnête.

---

## Comment l'utiliser (workflow automatisé)

1. L'Agent 09 te fournit 25 prompts répartis en 5 catégories (business directs, comparatifs, locaux, problème client, "meilleur [solution]").
2. L'**Agent 09bis (Auto-Test IA)** prend le relais automatiquement :
   - Il exécute les 25 prompts directement dans Claude (résultats **Confirmés**)
   - Il fait un Web Search Google pour chacun afin de capter les AI Overviews (résultats **Confirmés** ou **Estimés Haute**)
   - Il estime la réponse probable de ChatGPT, Perplexity et Gemini en analysant les sources publiques que ces IA citent en majorité (résultats **Estimés Haute / Moyenne / Faible**)
   - Il pré-remplit cette grille avec les statuts de confiance
3. Tu reçois ensuite une **shortlist de 5 à 10 prompts critiques** à tester manuellement sur ChatGPT / Perplexity / Gemini pour valider les estimations.
4. Tu colles tes validations dans les cases marquées "À valider manuellement". L'Agent 09 met à jour la roadmap priorisée.
5. Tu refais le test une fois par mois pour suivre l'évolution — l'Agent 09bis ré-exécute tout en moins de 15 minutes.

---

## Légende des colonnes

- **Prompt** : la requête exacte testée (copier-coller)
- **Plateforme** : ChatGPT / ChatGPT Search / Perplexity / Gemini / Claude / Google AI Overviews
- **Marque citée** : Oui / Non / À valider (ta marque apparaît-elle nommément dans la réponse ?)
- **Position** : 1ère mention / Milieu / Fin / Non citée
- **Lien donné** : URL exacte donnée par l'IA, ou "Aucun lien" si la marque est citée sans lien, ou "—" si non citée
- **Concurrents cités** : liste des concurrents nommés dans la réponse (séparés par virgule)
- **Source #1 citée** : domaine de la source la plus mise en avant par l'IA dans sa réponse (souvent en footnote ou en lien direct)
- **Statut de confiance** : Confirmé (test réel par l'agent) / Estimé Haute (3+ sources probables vérifiées) / Estimé Moyenne (1-2 sources vérifiées) / Estimé Faible (peu de sources accessibles) / À valider manuellement
- **Action correctrice** : ce qu'il faut faire pour améliorer la position sur ce prompt (rempli par l'Agent 09)

---

## Grille à remplir (pré-remplie par l'Agent 09bis)

| # | Prompt | Plateforme | Marque citée | Position | Lien donné | Concurrents cités | Source #1 citée | Statut de confiance | Action correctrice |
|---|--------|------------|--------------|----------|------------|-------------------|------------------|---------------------|--------------------|
| 1 | | Claude | | | | | | Confirmé | |
| 2 | | Google AIO | | | | | | Confirmé | |
| 3 | | ChatGPT | | | | | | Estimé Haute | |
| 4 | | Perplexity | | | | | | Estimé Moyenne | |
| 5 | | Gemini | | | | | | Estimé Faible | |
| 6 | | Claude | | | | | | Confirmé | |
| 7 | | Google AIO | | | | | | Confirmé | |
| 8 | | ChatGPT | | | | | | Estimé Haute | |
| 9 | | Perplexity | | | | | | Estimé Moyenne | |
| 10 | | Gemini | | | | | | Estimé Faible | |
| 11 | | Claude | | | | | | Confirmé | |
| 12 | | Google AIO | | | | | | Confirmé | |
| 13 | | ChatGPT | | | | | | À valider manuellement | |
| 14 | | Perplexity | | | | | | À valider manuellement | |
| 15 | | Gemini | | | | | | À valider manuellement | |
| 16 | | Claude | | | | | | Confirmé | |
| 17 | | Google AIO | | | | | | Confirmé | |
| 18 | | ChatGPT | | | | | | Estimé Haute | |
| 19 | | Perplexity | | | | | | Estimé Haute | |
| 20 | | Gemini | | | | | | Estimé Moyenne | |
| 21 | | Claude | | | | | | Confirmé | |
| 22 | | Google AIO | | | | | | Confirmé | |
| 23 | | ChatGPT | | | | | | À valider manuellement | |
| 24 | | Perplexity | | | | | | À valider manuellement | |
| 25 | | Gemini | | | | | | À valider manuellement | |

Note : la répartition Plateforme / Statut ci-dessus est indicative. L'Agent 09bis remplit avec les statuts réels selon ce qu'il a pu vérifier.

---

## Exemple de ligne remplie (par l'Agent 09bis)

| # | Prompt | Plateforme | Marque citée | Position | Lien donné | Concurrents cités | Source #1 citée | Statut de confiance | Action correctrice |
|---|--------|------------|--------------|----------|------------|-------------------|------------------|---------------------|--------------------|
| 1 | quel outil pour faire un audit SEO no-code en 2026 | Claude | Non | Non citée | — | Semrush, Ahrefs, Sitebulb | semrush.com | Confirmé | Créer une page comparative "audit SEO no-code" + soumettre un thread Reddit sur r/SEO |
| 2 | quel outil pour faire un audit SEO no-code en 2026 | Perplexity | À valider | — | — | Semrush, Ahrefs (estimés) | reddit.com/r/SEO (estimé) | Estimé Moyenne | À tester manuellement — IA prioritaire |

---

## Synthèse globale (pré-remplie par l'Agent 09bis)

### Score de Visibilité IA global
- Score sur 100 : __ / 100
- Intervalle de confiance : __ - __ / 100
- Détail pondéré : Claude __% · Google AIO __% · ChatGPT __% · Perplexity __% · Gemini __%

### Taux de citation
- Nombre de prompts où la marque est citée (Confirmé) : __ / __
- Nombre de prompts où la marque est probablement citée (Estimé Haute) : __ / __
- Nombre de prompts à valider manuellement : __ / __
- Taux de citation confirmé : __ %
- Taux de citation projeté (Confirmé + Estimé Haute) : __ %

### Plateforme la plus favorable
| Plateforme | Citations / 5 prompts testés |
|------------|------------------------------|
| ChatGPT | |
| ChatGPT Search | |
| Perplexity | |
| Gemini | |
| Claude | |
| Google AI Overviews | |

### Concurrents les plus cités à ta place
| Concurrent | Nombre de citations |
|------------|---------------------|
| | |
| | |
| | |

### Sources les plus citées dans les réponses IA (à conquérir)
| Source | Type (média / forum / annuaire / éditorial) | Nombre de citations | Stratégie d'entrée |
|--------|---------------------------------------------|---------------------|---------------------|
| | | | |
| | | | |

---

## Garde-fous d'utilisation

- Ne JAMAIS rejouer les mêmes prompts dans la même session IA (les IA conservent du contexte qui fausse le test). Ouvrir une nouvelle conversation pour chaque prompt.
- Ne JAMAIS forcer le nom de marque dans le prompt (ce serait une mesure de notoriété, pas de visibilité GEO).
- Ne JAMAIS attribuer une variation à une seule action — la visibilité GEO bouge lentement, comparer mois par mois.
- Toujours tester sur les mêmes plateformes d'un mois à l'autre pour avoir une base comparable.

---

## Cadence recommandée

- Test initial : à la première utilisation du pack (T0) — automatisé par l'Agent 09bis (15 min)
- Re-test : tous les mois (T+30, T+60, T+90...) — Agent 09bis relancé en autonome
- Re-test des prompts spécifiques après une action majeure (création d'une page comparative, thread Reddit, mention presse, etc.)
- Validation manuelle des 5-10 prompts critiques : 1 fois tous les 3 mois suffit

---

## Shortlist des prompts critiques à tester manuellement

L'Agent 09bis identifie automatiquement 5 à 10 prompts critiques pour lesquels une validation manuelle apporte beaucoup. Elle est listée ici :

| # | Prompt à tester | IA cible (1 seule) | Lien direct | Ce qu'il faut observer | Case grille à mettre à jour |
|---|-----------------|--------------------|-----------------|-----------------------|------------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |
| 9 | | | | | |
| 10 | | | | | |
