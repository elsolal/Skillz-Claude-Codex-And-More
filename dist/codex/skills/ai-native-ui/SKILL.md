---
name: ai-native-ui
description: Patterns et principes pour interfaces AI-natives (chat, copilots, agents). Couvre les invariants stables — message states (streaming/done/errored/interrupted), tool call lifecycle, citations inline, multi-modal composer, reasoning disclosure, permission gates. Framework-agnostic. Utiliser quand on construit du chat, copilot, assistant inline, ou interface agentique.
model: opus
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
user-invocable: true
---

# AI-Native UI

Patterns pour interfaces où **l'IA est un participant actif**, pas un feature isolé.

## Scope

**Couvert** (invariants stables) :
- Message states & lifecycle
- Tool call visualization
- Citations & sources inline
- Multi-modal composer
- Reasoning / thinking disclosure
- Permission gates avec memory
- Streaming UX
- Error recovery & retry

**Non-couvert** (fashion-driven, change tous les 3 mois) :
- Couleur exacte du dot streaming (→ `taste-skill`)
- Animation du curseur typing (→ `taste-skill`)
- Style des bubbles (→ `taste-skill`)
- Branding spécifique modèle

## Quand utiliser

- Construire un chat / copilot / assistant
- Refondre une interface AI existante
- Auditer les patterns AI d'un produit (gaps fonctionnels)
- Écrire les specs d'un produit AI-native

## 1. Message Lifecycle States

Tout message AI a un **état** explicite, pas juste "envoyé/reçu" :

| State | Visuel attendu | Interactions possibles |
|-------|----------------|------------------------|
| `pending` | Skeleton ou placeholder, pas de contenu | Annuler |
| `thinking` | Disclosure expandable (collapsed par défaut) | Annuler, expand reasoning |
| `streaming` | Texte qui apparaît token-par-token + cursor | Annuler, copy partial |
| `done` | Texte complet + actions (copy, regenerate, share, react) | Toutes |
| `errored` | Message d'erreur avec contexte + retry CTA | Retry, edit prompt, report |
| `interrupted` | Texte partiel + indicateur "stopped" + resume CTA | Resume, regenerate |
| `superseded` | Grisé (édité ou regenerated, version antérieure) | View history, restore |

**Règles** :
- ✅ État jamais ambigu (toujours visible)
- ✅ Transitions animées entre states (200-300ms)
- ✅ Action `cancel` accessible pendant `pending` / `thinking` / `streaming` (Esc keyboard)
- ✅ État persistant entre reload (pas de message qui se réinitialise)
- ❌ Jamais bloquer l'UI pendant `streaming` (composer reste enabled pour next message)

## 2. Tool Call Lifecycle

Chaque tool call a 4 états visuels :

```
┌─────────────────────────────────────────────────┐
│ 🔍 Reading file `src/auth.ts`            [▼]    │  ← collapsed by default
│    [Read • lines 1-200]                          │
└─────────────────────────────────────────────────┘

États :
- proposed   : "About to call X with args Y" (si permission required)
- running    : spinner + tool name + args (collapsed)
- completed  : checkmark + duration + résultat (expandable)
- failed     : ❌ + error + retry option
- skipped    : grisé "user denied" ou "auto-skipped"
```

**Règles** :
- ✅ Tool calls collapsed par défaut (réduire le bruit)
- ✅ Expandable pour voir args + result complet
- ✅ Stream l'output du tool si possible (long-running)
- ✅ Tool name humanisé ("Reading file" vs "tool_use Read")
- ✅ Localisation visible (file:line, URL, query)
- ❌ Pas de tool call sans nom lisible
- ❌ Pas de result wall-of-text (toujours expandable + truncated)

## 3. Citations & Sources

Quand l'AI cite des sources, **chaque claim** doit pointer vers sa source :

```markdown
## Inline numbered citations
La fonction est définie dans `auth.ts` [^1] et appelée 3 fois [^2][^3][^4].

[^1]: src/auth.ts:42-58
[^2]: src/login.ts:12
[^3]: src/middleware.ts:88
[^4]: src/api/handler.ts:120

## Or expandable hover
<button class="citation">[1]</button>
→ on hover : popover avec excerpt + link to source
→ on click : ouvre la source en preview
```

**Règles** :
- ✅ Chaque claim factuel a une citation (web search, RAG, code reading)
- ✅ Citations cliquables (jump to source)
- ✅ Differentier sources : web (favicon), code (file path), doc (icon)
- ✅ Si pas de citation → marquer "no source" (pas de claim sans source)
- ❌ Pas de citation décorative (citer pour le plaisir)

## 4. Multi-Modal Composer

Composer = champ d'input. Composants attendus en 2026 :

```
┌─────────────────────────────────────────────────────────┐
│ [Drop zone for files / images]                          │
│                                                          │
│ [@] Mention   [#] Tag   [/] Command   [|] Multi-line    │
│                                                          │
│ Type your message...                                    │
│                                                          │
│ [📎 Attach] [🎤 Voice] [🖼️ Image] [Model: Opus 4.7 ▼]  │
│                                          [Send / ⌘↵]    │
└─────────────────────────────────────────────────────────┘
```

**Règles** :
- ✅ Multiline par défaut (Shift+Enter), Cmd/Ctrl+Enter pour send
- ✅ Drag & drop files anywhere (visible drop zone on drag)
- ✅ Paste image / file from clipboard
- ✅ Slash commands (`/`) avec autocomplete dropdown
- ✅ @ mentions (users, files, contexts)
- ✅ Model picker visible si multi-model
- ✅ Token count visible avant send (si limite proche)
- ✅ Composer enabled même pendant streaming (queue next message)
- ❌ Pas de Enter = send par défaut sur desktop (cause sends accidentels en multi-line)
- ❌ Pas de composer avec UNIQUEMENT du texte (multimodal = la baseline)

## 5. Reasoning / Thinking Disclosure

Quand le modèle "réfléchit" avant de répondre :

```
┌─────────────────────────────────────────────────┐
│ ▶ Thinking (8s)                              [📋] │  ← collapsed by default
└─────────────────────────────────────────────────┘

▼ après expand :
┌─────────────────────────────────────────────────┐
│ ▼ Thinking (8s)                              [📋] │
│   The user is asking about X. Let me consider...  │
│   First, I'll check if Y applies because Z.       │
│   ...                                              │
└─────────────────────────────────────────────────┘
```

**Règles** :
- ✅ Collapsed par défaut (sauf si user a toggle "always show")
- ✅ Duration visible quand collapsed
- ✅ Expandable + copyable
- ✅ Différencié visuellement de la réponse finale (italique, color muted, ou frame)
- ❌ Jamais imposer le reasoning au user (toujours optionnel)
- ❌ Pas de reasoning auto-scrollé (laisser user lire à son rythme)

## 6. Permission Gates avec Memory

Pour actions sensibles (file writes, API calls, payments) :

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Allow Claude to write `src/auth.ts` ?                 │
│                                                          │
│ The file will be modified with these changes:           │
│ [diff preview, expandable]                              │
│                                                          │
│ ┌──────────┐ ┌──────────┐ ┌────────────────────────┐  │
│ │ ✓ Allow  │ │ ✗ Deny   │ │ ✓ Allow always (this   │  │
│ │  once    │ │          │ │   project / file)       │  │
│ └──────────┘ └──────────┘ └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Règles** :
- ✅ Action **et son impact** clairs (preview du diff, query, URL)
- ✅ 3 options : once / deny / always (avec scope explicite)
- ✅ Memory persistante (configurable par user)
- ✅ Possibilité de revoir/révoquer les permissions accordées
- ✅ Granularité : par tool, par scope (project / file / endpoint)
- ❌ Jamais "allow always" comme option par défaut
- ❌ Pas de permission gate après l'action (must be before)

## 7. Streaming UX

```
- Token-by-token streaming visible (pas de wait global puis dump)
- Cursor blinking pendant streaming
- User peut scroll librement (ne pas auto-scroll si user a scrollé up)
- Bouton "Jump to bottom" si user scrolled away
- Action "Stop" toujours accessible (Esc keyboard)
- Si interrupt : preserve le partial + indicateur visuel
- Code blocks : streaming aussi (rendre incrémentalement)
- Markdown : rendre le markdown au fil de l'eau (pas attendre fin)
```

## 8. Error Recovery & Retry

```
Types d'erreurs et recovery attendu :

┌────────────────────┬─────────────────────────────────────┐
│ Type               │ Recovery action                     │
├────────────────────┼─────────────────────────────────────┤
│ Network timeout    │ Auto-retry 3x avec backoff + manual │
│ Rate limit         │ Show retry-after time + manual      │
│ Context too long   │ Suggest /compact ou edit            │
│ Tool failed        │ Show error + retry tool only        │
│ Model error        │ Switch model option + manual retry  │
│ Auth expired       │ Re-auth flow inline                 │
│ User cancelled     │ Resume from cancellation point      │
└────────────────────┴─────────────────────────────────────┘
```

**Règles** :
- ✅ Erreur jamais "An error occurred" (toujours typée + actionable)
- ✅ Recovery action visible directement (pas dans menu caché)
- ✅ Préserver le contexte (pas reset la conversation après erreur)
- ✅ Logs/diagnostics accessible pour debug

## 9. AI Governance Surface

À vérifier dans `design-audit` pour toute UI IA:

- AI marker visible quand une action ou réponse est générée par IA.
- Disclaimer bref quand la sortie peut être incertaine, sensible ou non déterministe.
- Explainability accessible: sources, citations, tool calls, ou résumé d'action selon le contexte.
- Feedback loop: thumbs, report, edit, regenerate, dismiss ou équivalent.
- Human control: stop, undo, permission gate, retry ciblé, fallback déterministe.
- Product value gate: l'IA résout un besoin réel; sinon proposer une interaction déterministe plus simple.

## Anti-patterns à éviter

- ❌ Chat infini sans persistance / sans branching
- ❌ Composer qui disable le send pendant streaming (impose serial UX)
- ❌ Tool calls invisibles (UX qui prétend que "l'AI a juste répondu")
- ❌ Reasoning forcé visible (dilue la réponse)
- ❌ Citations sans cliquables (juste pour décorer)
- ❌ Permission gates groupées ("Allow all of these 5 actions" → all-or-nothing)
- ❌ Pas de regenerate (force "send another message" pour itérer)
- ❌ Pas de message history navigation (jump back to specific turn)

## Process

### 1. Audit gap (si projet existant)

```markdown
🤖 **AI-Native UI Audit**

**Project** : [name]
**Type** : [chat / copilot / inline assistant / agent]

| Pattern | Implemented | Gap |
|---------|-------------|-----|
| Message lifecycle 6+ states | [Y/N] | ... |
| Tool call viz collapsed | [Y/N] | ... |
| Inline citations | [Y/N] | ... |
| Multi-modal composer | [Y/N] | ... |
| Reasoning disclosure | [Y/N] | ... |
| Permission gates with memory | [Y/N] | ... |
| Streaming with interrupt | [Y/N] | ... |
| Typed error recovery | [Y/N] | ... |
| AI governance surface | [Y/N] | ... |
```

### 2. Spec write (si projet nouveau)

Créer `docs/planning/ai-ui/AI-UI-{slug}.md` avec sections par invariant.

### 3. Implementation guide

Pour chaque pattern, fournir :
- Composant requis (states, props)
- Wire frame ASCII
- Anti-patterns à bannir
- Reference (Claude.ai, ChatGPT, Cursor, Linear AI)

## Intégrations

| Workflow | Usage |
|----------|-------|
| `ui-designer` | Phase 0.5 — si projet AI, recommander ce skill au lieu/en plus de taste-skill |
| `pm-prd` | Si "AI", "chat", "copilot" dans le brief → auto-trigger pour spec |
| `figma-generate-design` | Loader ce skill pour mocker chat / composer |
| `figma-implement-design` | Reference pour les states |
| `taste-critic` | Compléter avec audit visual |
| `design-audit` | Gate UI IA: AI marker, disclaimer, explainability, feedback, human control |

## Output Validation

```markdown
### ✅ Checklist AI-Native UI

| Pattern | Spec'd | Implemented |
|---------|--------|-------------|
| Message states (6 minimum) | ✅/❌ | ✅/❌ |
| Tool call viz collapsed/expandable | ✅/❌ | ✅/❌ |
| Citations cliquables | ✅/❌ | ✅/❌ |
| Composer multi-modal + drag/drop | ✅/❌ | ✅/❌ |
| Reasoning collapsed by default | ✅/❌ | ✅/❌ |
| Permission gates avec memory | ✅/❌ | ✅/❌ |
| Streaming avec interrupt | ✅/❌ | ✅/❌ |
| Error recovery typé | ✅/❌ | ✅/❌ |
| AI governance surface | ✅/❌ | ✅/❌ |
```
