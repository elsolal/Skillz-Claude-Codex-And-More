---
description: Diagnostic complet de l'install Skillz-Claude. Vérifie symlinks providers (~/.gemini, ~/.codex, ~/.opencode, ~/.agents), drift du manifest, locks RALPH orphelins, frontmatter des specs, fichiers provider présents. Usage: /skillz-doctor [--fix]
---

# Skillz-Doctor — Health Check Install

**Session ID:** ${CLAUDE_SESSION_ID}

## Mode Diagnostic

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       SKILLZ-DOCTOR                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Health checks  → Symlinks       (.gemini, .codex, .opencode, .agents)  │
│                 → Manifest drift (skillz-manifest vs ~/.claude/skills/) │
│                 → RALPH locks    (sessions orphelines > 24h)            │
│                 → Spec frontmatter (status/approved_by valides)        │
│                 → Provider files (GEMINI.md, AGENTS.md, ext.json)      │
│                                                                          │
│  Output : table OK / WARN / FAIL + suggestion de fix par ligne          │
│  --fix  : applique les corrections automatiques sûres                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--fix` | false | Applique les corrections sûres (recreate symlinks cassés, purge RALPH locks > 7j) |
| `--verbose` | false | Affiche le détail de chaque check |
| `--scope` | all | `all`, `symlinks`, `manifest`, `ralph`, `specs`, `providers` |

---

## Checks à exécuter

### 1. Symlinks providers

Pour chaque provider (`.gemini`, `.codex`, `.opencode`, `.agents`) qui existe sous `~/` :

**Patterns valides** :
- **Single-symlink** : `~/.gemini/skills -> ~/.claude/skills` (tout le dossier est un lien)
- **Per-skill-symlinks** : `~/.codex/skills/` est un dossier réel qui contient des symlinks `<skill-name> -> ~/.claude/skills/<skill-name>` (1 symlink par skill)
- **Independent real dir** : `~/.agents/skills/` est un dossier réel avec ses propres skills (ex: `find-skills/` qui n'existe pas dans `~/.claude/skills/`)

**Pattern cassé** : `~/.X/skills/skills -> ../.claude/skills` — nested broken symlink causé par `ln -sf` dans un dossier existant.

```bash
for provider in .gemini .codex .opencode .agents; do
  dir="$HOME/$provider"
  [ -d "$dir" ] || continue

  link="$dir/skills"

  # Case 1: direct symlink
  if [ -L "$link" ]; then
    target=$(readlink "$link")
    if [ -e "$link" ]; then
      count=$(ls "$link" 2>/dev/null | wc -l | tr -d ' ')
      echo "OK   | $provider/skills → $target ($count skills)"
    else
      echo "FAIL | $provider/skills → $target (BROKEN)"
      echo "       FIX: rm -rf $link && ln -s $HOME/.claude/skills $link"
    fi

  # Case 2: real directory
  elif [ -d "$link" ]; then
    # 2a. Nested broken symlink (the bug we want to catch)
    if [ -L "$link/skills" ] && [ ! -e "$link/skills" ]; then
      echo "FAIL | $provider/skills/skills → $(readlink $link/skills) (BROKEN nested)"
      echo "       FIX: rm $link/skills  (keep $link/ for independent content)"
    else
      # 2b. Per-skill symlinks pattern (Codex-style) — count valid symlinks
      sym_count=$(find "$link" -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
      real_count=$(find "$link" -maxdepth 1 -type d -not -name "$(basename $link)" -not -name ".*" 2>/dev/null | wc -l | tr -d ' ')
      total=$((sym_count + real_count))
      if [ "$sym_count" -gt 5 ]; then
        echo "OK   | $provider/skills/ real dir, $sym_count per-skill symlinks (Codex pattern)"
      elif [ "$real_count" -gt 0 ]; then
        echo "OK   | $provider/skills/ real dir, $real_count independent skills (own content)"
      else
        echo "WARN | $provider/skills/ real dir, empty or unclear pattern"
      fi
    fi

  # Case 3: missing entirely
  else
    echo "WARN | $provider/skills missing entirely"
  fi

  # Knowledge check (same pattern, simpler)
  link="$dir/knowledge"
  if [ -L "$link" ] && [ -e "$link" ]; then
    echo "OK   | $provider/knowledge → $(readlink $link)"
  elif [ -L "$link" ]; then
    echo "FAIL | $provider/knowledge BROKEN"
  fi
done
```

**Si `--fix`** :
- Single-symlink cassé → recréer avec chemin absolu `~/.claude/skills`
- Nested broken symlink → `rm` du symlink cassé uniquement (garde le dossier parent intact)
- Ne jamais supprimer un dossier réel qui contient du contenu indépendant (.agents/skills/find-skills/)

### 2. Manifest drift

```bash
manifest="$HOME/.claude/.skillz-manifest"
[ -f "$manifest" ] || { echo "WARN | No manifest at $manifest — first install or pre-v5.x"; }

# Skills présents physiquement
present_skills=$(find "$HOME/.claude/skills" -mindepth 1 -maxdepth 1 -type d | xargs -n1 basename | sort)

# Skills listés dans le manifest
manifest_skills=$(grep '^skill:' "$manifest" | cut -d: -f2 | sort)

# Diff
extra=$(comm -23 <(echo "$present_skills") <(echo "$manifest_skills"))
missing=$(comm -13 <(echo "$present_skills") <(echo "$manifest_skills"))

[ -z "$extra" ] && [ -z "$missing" ] && echo "OK   | Manifest in sync"
[ -n "$extra" ] && echo "WARN | Skills présents non listés au manifest (user-added) : $extra"
[ -n "$missing" ] && echo "FAIL | Skills au manifest mais absents du disque : $missing"
```

**Si `--fix`** : ne PAS toucher au manifest (il est censé refléter le dernier install). Suggérer de relancer `./install.sh update claude`.

### 3. RALPH locks orphelins

```bash
logs_dir="docs/ralph-logs"
[ -d "$logs_dir" ] || { echo "OK   | No ralph-logs/ — pas d'historique"; return; }

# Sessions sans completion marker, modifiées il y a > 24h
for log in "$logs_dir"/*.md; do
  [ -f "$log" ] || continue
  last_mod=$(stat -f %m "$log" 2>/dev/null || stat -c %Y "$log")
  age_hours=$(( ($(date +%s) - last_mod) / 3600 ))

  if [ $age_hours -gt 24 ]; then
    if ! grep -q "COMPLETE\|CANCELLED\|TIMEOUT" "$log"; then
      echo "WARN | $log : session orpheline ($age_hours h, no completion marker)"
    fi
  fi
done
```

**Si `--fix`** : déplacer les logs orphelins > 7j vers `docs/ralph-logs/.archive/`.

### 4. Spec frontmatter

```bash
specs_dir="docs/planning/specs"
[ -d "$specs_dir" ] || { echo "OK   | No specs/ dir yet"; return; }

for spec in "$specs_dir"/*.md; do
  [ -f "$spec" ] || continue

  # Check frontmatter présent
  if ! head -1 "$spec" | grep -q '^---$'; then
    echo "FAIL | $spec : no frontmatter"
    continue
  fi

  # Champs obligatoires
  for field in title status approved_by approved_at slug; do
    if ! grep -q "^$field:" "$spec"; then
      echo "WARN | $spec : missing field '$field'"
    fi
  done

  # Status valide
  status=$(grep '^status:' "$spec" | cut -d: -f2 | xargs)
  case "$status" in
    draft|approved) ;;
    *) echo "FAIL | $spec : invalid status '$status' (expected: draft|approved)" ;;
  esac
done
```

**Si `--fix`** : ne PAS modifier les frontmatter automatiquement (risque d'auto-approbation par RALPH). Proposer le diff à l'utilisateur.

### 5. Provider files

Vérifier que chaque provider a son fichier d'instructions :

| Provider | Fichier attendu | Check |
|---|---|---|
| `~/.codex/` | `AGENTS.md` | présent et non vide |
| `~/.gemini/` | `GEMINI.md` | présent et non vide |
| `~/.opencode/` | `AGENTS.md` | présent et non vide |
| `~/.agents/` | `AGENTS.md` | présent et non vide |

Si manquant : `WARN | Provider $X exists but no instruction file`.

---

## Format de sortie

```
🩺 Skillz-Doctor — Health Report

✅ 12 OK     ⚠️  3 WARN     ❌ 1 FAIL

──────────────────────────────────────────────────────────────────
SYMLINKS
──────────────────────────────────────────────────────────────────
✅ .codex/skills      → /Users/aymeric/.claude/skills (47 skills)
✅ .opencode/skills   → ../.claude/skills
❌ .gemini/skills     → real dir with broken nested symlink
   FIX: rm -rf ~/.gemini/skills && ln -s ~/.claude/skills ~/.gemini/skills
✅ .agents/skills     → real dir (intentional, contains find-skills)

──────────────────────────────────────────────────────────────────
MANIFEST
──────────────────────────────────────────────────────────────────
⚠️  3 user-added skills not in manifest: my-custom, foo, bar

──────────────────────────────────────────────────────────────────
RALPH LOCKS
──────────────────────────────────────────────────────────────────
⚠️  docs/ralph-logs/abc123.md : session orpheline (72h, no completion marker)

──────────────────────────────────────────────────────────────────
SPECS
──────────────────────────────────────────────────────────────────
✅ All 5 specs have valid frontmatter

──────────────────────────────────────────────────────────────────
PROVIDERS
──────────────────────────────────────────────────────────────────
✅ All provider instruction files present

──────────────────────────────────────────────────────────────────
NEXT
──────────────────────────────────────────────────────────────────
Run with --fix to apply the 1 safe correction (Gemini symlink).
Manual review needed for: manifest user-skills, ralph orphans.
```

---

## Démarrage

Arguments : **$ARGUMENTS**

J'analyse l'état d'install et je produis le rapport.

1. Détecter le scope (`--scope` ou `all` par défaut)
2. Exécuter les checks Bash dans l'ordre ci-dessus
3. Compter OK/WARN/FAIL
4. Produire le rapport au format ci-dessus
5. Si `--fix` passé : appliquer uniquement les corrections sûres (symlinks cassés, archive RALPH > 7j) et reporter
