# Polices embarquées

Aucune police n'est supposée installée sur la machine de l'acheteur, et aucun import distant n'est autorisé dans le HTML final. Les deux familles sont donc livrées ici.

| Famille | Rôle | Licence | Fichiers |
|---|---|---|---|
| **Inter** | Titres et corps de texte | OFL 1.1 — `OFL-Inter.txt` | `Inter-latin.woff2`, `Inter-latin-ext.woff2` |
| **JetBrains Mono** | Snippets et blocs de code | OFL 1.1 — `OFL-JetBrainsMono.txt` | `JetBrainsMono-latin.woff2`, `JetBrainsMono-latin-ext.woff2` |

Les deux sont des **polices variables** : un seul fichier couvre les graisses 100 à 900, dont Regular 400, Medium 500, SemiBold 600, Bold 700 et ExtraBold 800. Les sous-ensembles `latin` et `latin-ext` couvrent le français, les guillemets typographiques et les langues d'Europe centrale.

## Comment les utiliser dans le HTML du livrable

Le fichier **`fonts.css`** contient les quatre règles `@font-face` avec les polices déjà encodées en base64. C'est la seule méthode fiable : le HTML d'un livrable est écrit dans le dossier projet du client, hors du kit, donc un chemin relatif vers ce dossier serait cassé.

Copier le contenu de `fonts.css` en tête du `<style>` du document, puis déclarer :

```css
body   { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.snippet { font-family: 'JetBrains Mono', Menlo, Monaco, Consolas, monospace; }
```

Le document devient autonome : il se rend à l'identique sur une machine hors ligne, sans aucune police installée.

## Licences

Les deux familles sont sous **SIL Open Font License 1.1**, qui autorise l'usage commercial, l'embarquement et la redistribution. Les textes de licence doivent rester livrés avec le kit : ne pas supprimer `OFL-Inter.txt` ni `OFL-JetBrainsMono.txt`.
