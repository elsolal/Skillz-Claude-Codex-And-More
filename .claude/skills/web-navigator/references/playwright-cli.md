# Playwright CLI

## Source externe

`@playwright/cli` est le runtime recommande pour ce skill. Le package installe un skill officiel `playwright-cli` avec:

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills
playwright-cli --help
```

`playwright-cli install --skills` cible Claude par defaut. Utiliser `playwright-cli install --skills=agents` pour installer le skill compagnon dans un dossier agents generique quand l'environnement le supporte.

Le package local inspecte pendant l'integration etait `@playwright/cli` `0.1.14`, license Apache-2.0, repository `microsoft/playwright-cli`.

## Pourquoi CLI plutot que MCP par defaut

Le README upstream explique que le CLI est adapte aux coding agents parce que les commandes terminal sont plus compactes que de grands schemas MCP et de gros arbres d'accessibilite. Dans Skillz-Claude, on garde cette logique:

- CLI pour actions courtes, preuves ciblees et faible cout contexte.
- MCP/navigateur integre si l'environnement offre une meilleure introspection ou une session persistante deja active.
- WebFetch pour contenu public statique quand une navigation browser n'apporte rien.

## Commandes utiles

```bash
playwright-cli open <url>
playwright-cli goto <url>
playwright-cli snapshot
playwright-cli screenshot --filename=/tmp/page.png
playwright-cli console
playwright-cli requests
playwright-cli request <index>
playwright-cli resize 390 844
playwright-cli tab-list
playwright-cli tab-new <url>
playwright-cli generate-locator <target> --raw
playwright-cli eval "document.title"
```

Pour les sessions:

```bash
playwright-cli list
playwright-cli close-all
playwright-cli kill-all
PLAYWRIGHT_CLI_SESSION=site-audit <agent-command>
```

Pour un login de test:

```bash
playwright-cli state-save /tmp/skillz-web-auth.json
playwright-cli state-load /tmp/skillz-web-auth.json
```

## Regles Skillz-Claude

- Toujours lancer `playwright-cli --help` si un doute existe sur les options installees.
- Preferer `--raw` ou `--json` quand la sortie doit etre pipee, comparee ou resumee.
- Utiliser `snapshot` pour obtenir les refs d'elements avant `click`, `fill`, `hover`, `check`.
- Stocker screenshots, PDFs, traces et auth state hors repo ou dans un dossier ignore.
- Fermer les sessions apres usage si elles ne servent plus: `playwright-cli close` ou `close-all`.
