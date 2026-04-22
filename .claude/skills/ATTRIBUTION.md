# Skills Attribution

This directory bundles skills authored by third parties. We mirror them into Skillz-Claude so they propagate through `install.sh` to every supported provider (Claude / Codex / Gemini / OpenCode / generic agents).

## Taste Skills (Leonxlnx/taste-skill)

The following 9 skills are integrated from [github.com/Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) by Leonxlnx, with the goal of giving the AI good frontend "taste" and blocking generic anti-patterns ("slop").

| Folder | Frontmatter `name` | Source path |
|--------|-------------------|-------------|
| `brutalist-skill/` | `industrial-brutalist-ui` | `skills/brutalist-skill/SKILL.md` |
| `gpt-tasteskill/` | `gpt-taste` | `skills/gpt-tasteskill/SKILL.md` |
| `images-taste-skill/` | `image-taste-frontend` | `skills/images-taste-skill/SKILL.md` |
| `minimalist-skill/` | `minimalist-ui` | `skills/minimalist-skill/SKILL.md` |
| `output-skill/` | `full-output-enforcement` | `skills/output-skill/SKILL.md` |
| `redesign-skill/` | `redesign-existing-projects` | `skills/redesign-skill/SKILL.md` |
| `soft-skill/` | `high-end-visual-design` | `skills/soft-skill/SKILL.md` |
| `stitch-skill/` | `stitch-design-taste` | `skills/stitch-skill/{SKILL.md,DESIGN.md}` |
| `taste-skill/` | `design-taste-frontend` | `skills/taste-skill/SKILL.md` |

**Upstream** : https://github.com/Leonxlnx/taste-skill
**Author** : Leonxlnx ([@lexnlin](https://x.com/lexnlin)), Blueemi ([@blueemi99](https://x.com/blueemi99))
**Website** : https://tasteskill.dev

### Updating

To pull upstream changes :

```bash
cd /tmp && rm -rf taste-skill && git clone --depth 1 https://github.com/Leonxlnx/taste-skill.git
# Diff against current copy :
diff -r /tmp/taste-skill/skills/ .claude/skills/ | grep -E "^(Only in /tmp|diff)" | head
# Apply selectively (use cp for skills you want to refresh)
```

### Companion skill (Skillz-Claude original)

`taste-router/` — meta-skill that picks the right taste-skill + dial values from a brief. Authored locally, not from upstream.
