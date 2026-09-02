---
name: landing-copy
description: Écrit du copy de landing page premium — H1 avec sujet + bénéfice mesurable, value props concrets, social proof, CTA hierarchy, FAQ. Bannit les filler corporate ("Discover", "leverage", "amazing", "experience"). Patterns Julian Shapiro / Stripe / Linear / Cal.com. Utiliser pour landing marketing, pricing pages, product pages.
model: opus
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
user-invocable: true
---

# Landing Copy

Écrire du copy de landing page qui convertit, sans bullshit corporate.

## Scope

**Couvert** :
- Hero (H1, subhead, CTA, visual placement)
- Value propositions (3-6 cards)
- Social proof (logos, testimonials, metrics)
- Feature sections
- Pricing page copy
- CTA hierarchy
- FAQ
- Footer copy meaningful

**Non-couvert** :
- Microcopy in-product (→ `product-microcopy`)
- Long-form blog (→ skill futur `blog-writer`)
- Email copy (→ skill futur `email-copy`)
- SEO meta + schema (→ peut être ajouté ici si demande)

## Quand utiliser

- Brief "landing page", "marketing site", "product page", "pricing"
- Audit copy d'une landing existante
- Iteration A/B sur des hero variants
- Avant `figma-implement-design` si la landing est visuelle uniquement

## Anti-patterns à BANNIR (les défauts AI)

### Mots interdits dans H1/H2/CTA
- "Discover", "Explore", "Unlock", "Experience", "Elevate", "Transform"
- "Amazing", "Powerful", "Seamless", "Revolutionary", "Cutting-edge", "Best-in-class"
- "Solution(s)", "Platform" (sauf si vraiment platform), "Synergy", "Leverage"
- "Empower", "Enable", "Accelerate"
- "Innovative", "Next-generation", "World-class"
- "Effortless", "Intuitive" (à montrer, pas à dire)

### Patterns interdits
- ❌ H1 vague : "The future of [X]" / "[X] reimagined" / "[X] for the modern team"
- ❌ Subhead qui répète le H1 sans ajouter d'info
- ❌ Value props 3 cards génériques : "Fast / Reliable / Beautiful"
- ❌ Social proof vague : "Trusted by thousands" sans logos OU sans nombre précis
- ❌ Testimonials sans nom + photo + role + company
- ❌ "Get started for free" comme unique CTA (implicite : on demande le CC)
- ❌ Pricing avec "Contact us" caché en bas
- ❌ FAQ qui répète le marketing (pas de vraies questions client)
- ❌ Hero avec mockup générique de browser/MacBook flottant

## Patterns à FAVORISER

### H1 : sujet + bénéfice mesurable
**Format** : `[Verbe action / Sujet] [bénéfice spécifique avec metric ou qualifier concret]`

**Bons** :
- "Ship 10× faster with AI agents that write your code" (Cursor)
- "Set up payments in 7 minutes" (Stripe-style)
- "Cancel meetings, not your day" (Cal.com vibe)
- "Your project manager replaced by 5 lines of YAML" (provocateur, claim mesurable)

**Mauvais** :
- "AI for everyone" (vague, pas de bénéfice)
- "The future of payments" (futur ≠ maintenant, pas de claim)
- "Discover the power of automation" (verbes faibles + cliché)

### Subhead : context + différenciation
- 1-2 phrases (pas plus)
- Réponds à "OK et alors ?" du H1
- Si possible : un nom/concept clé + différenciant vs alternative

**Bon** : "Run any model — Claude, GPT, Gemini — through one API. Pay per token, no commitments, change provider in 2 lines."

### CTA primary
- Verbe action concret
- Indique ce qui se passe après le clic

**Bons** : "Start in 7 minutes", "See pricing", "Get API key", "Book a 15-min demo"
**Mauvais** : "Get started", "Learn more", "Sign up", "Try it free" (sans contexte)

### CTA secondary
- Toujours moins voyant (variant ghost / outline)
- Alternative pour les hesitants : "See live demo", "Read the docs", "Watch 2-min video"

### Value props (3-6 cards)
**Format** : `[Headline avec metric ou claim concret] · [1-2 phrases qui prouvent] · [optional: link to deep dive]`

**Bonnes** :
- "Deploys in 30 seconds — Connect your repo, push to main, live URL. No Dockerfile."
- "$0 until you hit 10k requests/mo — Then $0.001/req. No seats, no minimum."

**Mauvaises** :
- "Fast — Lightning quick performance you'll love"
- "Reliable — Built to last with enterprise-grade infrastructure"

### Social proof
- ✅ Logos visibles (5-8 max, alignés, monochrome ou color cohérent)
- ✅ Metric précis : "12,847 developers ship daily with us"
- ✅ Testimonials avec nom + photo + role + company + 1-2 phrases concrètes
- ❌ "G2 Leader 2024" sans contexte
- ❌ Stars rating générique sans source

### Pricing page
- ✅ Tier names parlants (pas "Starter / Pro / Enterprise" sans plus)
- ✅ Prix visibles immédiatement (pas "Contact for pricing" sauf vraie raison)
- ✅ Différence entre tiers en 1 mot/phrase (pas wall of text)
- ✅ FAQ pricing dédiée
- ✅ "What's not included" listé
- ❌ Plus de 4 tiers (paralyse la décision)

### FAQ
**Vraies questions client** (pas du marketing déguisé) :
- "How does this compare to [concurrent connu] ?"
- "What happens if I exceed my plan ?"
- "Is my data used for training ?"
- "Can I cancel anytime ?"
- "Do you have an enterprise/SSO/SOC2 plan ?"
- "What if [edge case fréquent] ?"

**Non** :
- "Why choose [product] ?" → c'est ton job de le montrer ailleurs
- "Is [product] easy to use ?" → réponse forcément biaisée

## Process

### 1. Brief intake

```markdown
✍️ **Landing Copy**

**Product** : [name]
**One-liner pitch** : [1 phrase]
**Audience cible** : [persona — devs / PMs / designers / etc.]
**Concurrent direct** : [si connu]
**Différenciation clé** : [vs concurrent — 1 phrase]
**Tone voice** : [serious / playful / technical / sales-y]
**Conversion goal** : [signup free / demo / contact sales / docs]
**Contraintes** : [SEO keywords obligatoires, claims légaux, etc.]
```

### 2. Inventory de la landing (si refonte)

`Glob` les fichiers landing existants, identifier :
- H1 actuel + score (sur les critères ci-dessus)
- CTAs (count + variants)
- Social proof (forme actuelle)
- Faiblesses concrètes

### 3. Draft V1

Écrire la copy en suivant la structure :

```markdown
## Hero
**H1** : [...]
**Subhead** : [...]
**CTA primary** : [...]
**CTA secondary** : [...]
**Visual** : [description du visual qui doit accompagner]

## Social proof bar
**Format** : [logos / metric / mix]
**Metric/text** : [...]
**Logos suggérés** : [...]

## Value props
### Card 1
**Headline** : [...]
**Body** : [...]
**Link** : [...]

[répéter 3-6 fois]

## Feature sections (1-3 deep dives)
### Section 1
**Eyebrow** : [kicker au-dessus du H2]
**H2** : [...]
**Body** : [2-3 paragraphes max]
**CTA inline** : [...]
**Visual** : [description]

## Pricing (si applicable)
[tiers + prix + features per tier]

## FAQ
**Q1** : [vraie question client]
**A1** : [...]
[6-10 questions]

## Final CTA section
**H2** : [...]
**CTA** : [...]
```

### 4. Validation

```markdown
### ✅ Checklist Landing Copy

| Critère | Status |
|---------|--------|
| H1 contient sujet + bénéfice mesurable | ✅/❌ |
| Aucun mot interdit (Discover, Amazing, etc.) | ✅/❌ |
| CTA primary indique ce qui se passe après clic | ✅/❌ |
| Value props ont metric ou claim concret | ✅/❌ |
| Social proof avec metric précis OU logos visibles | ✅/❌ |
| Testimonials avec nom + photo + role + company | ✅/❌ |
| FAQ contient vraies questions client (pas marketing déguisé) | ✅/❌ |
| Différenciation vs concurrent claire | ✅/❌ |
| Tone voice cohérent partout | ✅/❌ |
```

### 5. Variants pour A/B (optionnel)

Si demandé, produire 2-3 variants de H1/CTA pour A/B test, avec hypothèse explicite :
- **Variant A** : appel à l'identité ("For devs who hate YAML")
- **Variant B** : metric ("Set up in 7 min")
- **Variant C** : provocateur ("Replace your DevOps team")
- Hypothèse : Variant B convertira mieux sur cold traffic, A sur warm.

## Intégrations

| Workflow | Insertion |
|----------|-----------|
| `ui-designer` | Phase 0.5 — si projet marketing, suggérer landing-copy avant les composants |
| `pm-prd` | Si "landing", "marketing site" → trigger après le PRD |
| `figma-implement-design` | Loader ce skill avant impl si copy générique détecté dans le Figma |
| `taste-critic` | Cross-check : si taste-critic flag des H1 wrappés sur 6 lignes, c'est souvent que le copy est trop long aussi |

## Sources / inspiration

- Julian Shapiro — Marketing primitives
- Stripe blog (copy style)
- Linear changelog (anti-corporate)
- Cal.com homepage (provocation calibrée)
- Kontra — landing patterns
- Patrick McKenzie — copywriting essays
