# Troubleshooting Guide

> Solutions aux problèmes courants avec le workflow D-EPCT+R

---

## 🩺 Premier réflexe : `/skillz-doctor`

Avant de creuser un problème manuellement, lance le diagnostic automatique :

```bash
/skillz-doctor           # rapport complet (symlinks, manifest, specs, providers)
/skillz-doctor --fix     # corrections sûres automatiques
```

Il couvre les 5 sources de panne les plus fréquentes :
- **Symlinks providers cassés** (ex: `~/.gemini/skills/skills` nested broken — le bug historique)
- **Manifest drift** (skill disparu sur disque mais encore au manifest)
- **RALPH locks orphelins** (sessions > 24h sans completion)
- **Spec frontmatter invalide** (`/auto-dev` refuse de démarrer)
- **Provider files manquants** (`GEMINI.md`, `AGENTS.md` absents)

Si `/skillz-doctor` ne trouve rien, continue avec les sections ci-dessous.

---

## Table des matières

1. [Phase Planning](#phase-planning)
2. [Phase Développement](#phase-développement)
3. [Mode RALPH](#mode-ralph)
4. [Problèmes généraux](#problèmes-généraux)
5. [Install / Symlinks / Providers](#install--symlinks--providers)

---

## Phase Planning

### Brainstorm bloqué

**Symptôme:** L'idée reste vague, pas de direction claire.

**Solutions:**
1. **Changer de mode** : Si en mode Creative, passer en Research-first
   ```
   "Passons en mode research-first pour valider quelques hypothèses"
   ```

2. **Utiliser Five Whys** : Creuser le "pourquoi" 5 fois
   ```
   - Pourquoi ce problème existe ?
   - Pourquoi [réponse 1] ?
   - Pourquoi [réponse 2] ?
   - ...
   ```

3. **SCAMPER** : Forcer la créativité
   - **S**ubstitute : Que peut-on remplacer ?
   - **C**ombine : Que peut-on combiner ?
   - **A**dapt : Que peut-on adapter d'ailleurs ?
   - **M**odify : Que peut-on modifier/amplifier ?
   - **P**ut to other use : Autre usage ?
   - **E**liminate : Que peut-on supprimer ?
   - **R**everse : Et si on faisait l'inverse ?

4. **Time-box** : Se donner 10 minutes max, puis décider

---

### PRD trop vague

**Symptôme:** Le scope n'est pas clair, trop de "ça dépend".

**Solutions:**
1. **Forcer les décisions** :
   ```
   "Pour chaque 'ça dépend', choisissons une option par défaut"
   ```

2. **MoSCoW stricte** :
   - **Must have** : Sans ça, pas de MVP
   - **Should have** : Important mais pas bloquant
   - **Could have** : Nice to have
   - **Won't have** : Explicitement hors scope

3. **Réduire le scope** :
   ```
   "Quel est le PLUS PETIT livrable qui apporte de la valeur ?"
   ```

4. **Poser des contraintes** :
   - Budget temps : "Maximum 3 jours"
   - Budget features : "Maximum 5 stories"

---

### Architecture trop complexe

**Symptôme:** Over-engineering, trop de composants.

**Solutions:**
1. **Appliquer YAGNI** :
   ```
   "Est-ce qu'on a VRAIMENT besoin de ça pour le MVP ?"
   ```

2. **Boring technology** :
   - Préférer les technos éprouvées
   - Éviter les nouveautés pour le MVP

3. **Monolithe d'abord** :
   ```
   "Commençons par un monolithe, on splittera si besoin"
   ```

4. **Moins de couches** :
   - Pas besoin de repository pattern pour un CRUD
   - Pas besoin de microservices pour < 10 users

---

### Stories non-INVEST

**Symptôme:** Stories trop grosses, dépendantes, non testables.

**Solutions:**
1. **Découper les XL** :
   ```
   "Cette story fait trop de choses. Découpons par :
   - Fonctionnalité (CRUD séparé)
   - Utilisateur (admin vs user)
   - Plateforme (web vs mobile)
   - Scénario (happy path vs edge cases)"
   ```

2. **Rendre testable** :
   ```
   "Ajoutons des critères Given/When/Then"
   ```

3. **Éliminer les dépendances** :
   ```
   "Cette story peut-elle être livrée seule ?"
   ```

---

## Phase Développement

### Explain incomplet

**Symptôme:** L'architecture du code n'est pas claire.

**Solutions:**
1. **Demander plus de contexte** :
   ```
   "Montre-moi les fichiers liés à [feature]"
   "Où est défini [composant] ?"
   ```

2. **Tracer un flow** :
   ```
   "Trace le parcours d'une requête de A à Z"
   ```

3. **Identifier les patterns** :
   ```
   "Quels patterns sont utilisés dans ce projet ?"
   "Comment sont structurés les autres [composants similaires] ?"
   ```

---

### Plan rejeté

**Symptôme:** Le plan d'implémentation n'est pas satisfaisant.

**Solutions:**
1. **Demander des alternatives** :
   ```
   "Propose 2 autres approches"
   ```

2. **Challenger les étapes** :
   ```
   "Cette étape peut-elle être simplifiée ?"
   "Peut-on merger les étapes 2 et 3 ?"
   ```

3. **Ajouter des contraintes** :
   ```
   "Le plan doit tenir en 5 étapes max"
   ```

---

### Code ne compile pas (Lint/Types)

**Symptôme:** Erreurs de lint ou de types après implémentation.

**Solutions:**
1. **Fixer immédiatement** :
   ```
   "Fix les erreurs de lint/types avant de continuer"
   ```

2. **Comprendre l'erreur** :
   ```
   "Explique cette erreur TypeScript et propose une solution"
   ```

3. **Vérifier les imports** :
   ```
   "Vérifie que tous les imports sont corrects"
   ```

**Prévention:**
- Toujours run `npm run lint` et `npm run typecheck` après chaque étape
- Configurer le pre-commit hook

---

### Tests flaky

**Symptôme:** Tests qui passent parfois, échouent parfois.

**Solutions:**
1. **Identifier la cause** :
   ```
   "Run le test 10 fois et identifie le pattern d'échec"
   ```

2. **Causes courantes** :
   - **Timing** : Ajouter des `waitFor`, éviter `sleep`
   - **State partagé** : Isoler les tests
   - **Network** : Mocker les appels API
   - **Random data** : Utiliser des seeds

3. **Pattern de fix** :
   ```typescript
   // ❌ Mauvais
   await page.click('button');
   expect(result).toBe(true);

   // ✅ Bon
   await page.click('button');
   await expect(page.locator('.result')).toBeVisible();
   ```

---

### Review bloquée

**Symptôme:** La review ne passe pas (correctness, readability, performance).

**Solutions:**

**Pass 1 - Correctness:**
```
"Vérifie que :
- Le code fait ce qui est demandé
- Les edge cases sont gérés
- Pas de bugs évidents"
```

**Pass 2 - Readability:**
```
"Améliore :
- Les noms de variables/fonctions
- La structure du code
- Les commentaires si nécessaires"
```

**Pass 3 - Performance:**
```
"Optimise :
- Les queries N+1
- Les re-renders inutiles
- Les calculs coûteux"
```

---

## Mode RALPH

### RALPH ne s'arrête pas

**Symptôme:** La boucle continue sans atteindre la completion promise.

**Solutions:**
1. **Vérifier la promise** :
   ```
   "Est-ce que 'DONE' ou 'FEATURE COMPLETE' est bien affiché ?"
   ```

2. **Arrêter manuellement** :
   ```
   /cancel-ralph
   ```

3. **Vérifier les logs** :
   ```
   cat docs/ralph-logs/[date]-*.md
   ```

4. **Réduire le scope** :
   ```
   "Simplifie l'objectif pour atteindre une completion"
   ```

---

### RALPH bloqué sur une erreur

**Symptôme:** RALPH itère sans progresser.

**Solutions:**
1. **Lire le log** :
   ```
   tail -50 docs/ralph-logs/[date]-*.md
   ```

2. **Intervenir** :
   ```
   /cancel-ralph
   # Fixer le problème manuellement
   /auto-loop "Continue depuis [étape]"
   ```

3. **Changer d'approche** :
   ```
   "L'approche actuelle ne fonctionne pas. Essaie [alternative]"
   ```

---

### RALPH timeout

**Symptôme:** Le timeout est atteint avant completion.

**Solutions:**
1. **Augmenter le timeout** :
   ```
   /auto-dev #123 --timeout 3h
   ```

2. **Découper la tâche** :
   ```
   /auto-dev #123-part1 --max 20
   /auto-dev #123-part2 --max 20
   ```

3. **Passer en mode manuel** :
   ```
   /dev #123
   # Valider manuellement chaque étape
   ```

---

## Problèmes généraux

### Claude ne trouve pas les fichiers

**Symptôme:** "File not found" ou contexte manquant.

**Solutions:**
1. **Vérifier le chemin** :
   ```
   "Liste les fichiers dans [dossier]"
   ```

2. **Donner plus de contexte** :
   ```
   "Le fichier est dans src/components/..."
   ```

3. **Utiliser des patterns** :
   ```
   "Trouve tous les fichiers *.tsx dans src/"
   ```

---

### Skill non reconnu

**Symptôme:** La commande ne déclenche pas le bon skill.

**Solutions:**
1. **Utiliser la commande exacte** :
   ```
   /discovery
   /dev #123
   /auto-loop "prompt"
   ```

2. **Vérifier l'installation** :
   ```
   ls .claude/skills/
   ls .claude/commands/
   ```

3. **Réinstaller** :
   ```
   curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- .
   ```

---

### Contexte perdu

**Symptôme:** Claude "oublie" ce qui a été fait.

**Solutions:**
1. **Résumer le contexte** :
   ```
   "Rappel : on travaille sur [feature], on en est à [étape]"
   ```

2. **Pointer vers les docs** :
   ```
   "Lis docs/planning/prd/[projet].md pour le contexte"
   ```

3. **Utiliser les issues** :
   ```
   "Voir GitHub issue #123 pour les requirements"
   ```

---

## Install / Symlinks / Providers

### Gemini/OpenCode/Agents ne voit pas mes skills après install

**Symptôme:** Les skills sont dans `~/.claude/skills/` mais un provider les ignore.

**Cause la plus fréquente:** Nested broken symlink `~/.X/skills/skills` créé quand `install.sh` a lancé `ln -sf ../.claude/skills ~/.X/skills` alors que `~/.X/skills` existait déjà comme dossier réel. Le lien finit créé **à l'intérieur** du dossier, avec un path relatif qui ne résout plus.

**Fix rapide:**
```bash
/skillz-doctor --fix
```

**Fix manuel (si tu préfères inspecter d'abord):**
```bash
# Pour Gemini (single-symlink pattern)
rm -rf ~/.gemini/skills
ln -s ~/.claude/skills ~/.gemini/skills

# Pour .agents (dossier réel indépendant — supprimer seulement le nested cassé)
rm ~/.agents/skills/skills
```

**Prévention:** v5.8.0+, préférer l'install natif par provider (`claude --plugin-dir`, `gemini --extension-dir`) plutôt que `install.sh` pour éviter les symlinks locaux.

### `/auto-dev` refuse de démarrer

**Symptôme:** `Pre-flight gate échoué : pas de mandat clair pour /auto-dev`.

**Cause:** Ce n'est pas un bug, c'est une safety gate v5.7.0+. RALPH refuse de coder en autonome sans mandat humain.

**Solutions:**
1. **Passer une issue GitHub:** `/auto-dev #123`
2. **Approuver une spec:** dans `docs/planning/specs/<date>-<slug>-design.md`, mettre `status: approved` + `approved_by: <ton nom>` (pas "ralph")
3. **Override pour prototypage:** `/auto-dev --allow-no-spec "description"` (loggé comme non-recommandé)

### CHANGELOG pas modifié → `/ship` s'arrête

**Symptôme:** `/ship` abort en Step 1.

**Cause:** Verification-before-completion v5.7.0+ exige un CHANGELOG modifié pour `/ship`.

**Fix:**
```bash
# Ajouter une entrée manuellement OU laisser /ship la générer
/ship
# En cas d'abort: éditer CHANGELOG.md puis relancer
```

### Plugin Claude ne se charge pas

**Symptôme:** `claude --plugin-dir ./Skillz-Claude` ne montre pas les skills.

**Checks:**
1. `.claude-plugin/plugin.json` existe au repo root ? `cat .claude-plugin/plugin.json`
2. Les symlinks `skills/`, `commands/` à la racine résolvent ? `ls -la skills`
3. Version de Claude Code supporte les plugins ? Sinon mettre à jour : `claude --version`
4. Namespace correct ? Les skills du plugin sont namespacés `/skillz-claude:nom-du-skill`

### Extension Gemini ne charge pas GEMINI.md

**Symptôme:** `gemini --extension-dir ./Skillz-Claude` ne lit pas le contexte.

**Checks:**
1. `gemini-extension.json` existe au repo root et contient `"contextFileName": "GEMINI.md"` ?
2. `GEMINI.md` existe au repo root (pas seulement dans `.gemini/`) ?
3. Redémarrer Gemini CLI après changement de manifest

---

## Aide supplémentaire

Si le problème persiste :

1. **Lancer `/skillz-doctor`** : diagnostic automatique (première étape)
2. **Vérifier les logs RALPH** : `docs/ralph-logs/`
3. **Lire la doc** : `docs/GUIDE-COMPLET.md`
4. **Ouvrir une issue** : https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues
