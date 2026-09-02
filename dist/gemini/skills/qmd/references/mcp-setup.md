# QMD MCP Server Setup

## Install

```bash
npm install -g @tobilu/qmd  # requires Node 22+
# or: bun install -g @tobilu/qmd
qmd collection add ~/path/to/markdown --name myknowledge --mask "**/*.md"
qmd context add qmd://myknowledge "Project memory, documentation, and durable knowledge"
qmd update
qmd embed
```

## Configure MCP Client

**Claude Code** (`~/.claude/mcp.json` or project `.mcp.json`):
```json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp"] }
  }
}
```

Claude Code user scope can also be configured with:

```bash
claude mcp add --transport stdio --scope user qmd -- qmd mcp
```

**Codex** (`~/.codex/config.toml`):
```toml
[mcp_servers.qmd]
command = "qmd"
args = ["mcp"]
```

**OpenCode** (`~/.config/opencode/opencode.json`):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "qmd": {
      "type": "local",
      "command": ["qmd", "mcp"],
      "enabled": true
    }
  }
}
```

## HTTP Mode

```bash
qmd mcp --http              # Port 8181
qmd mcp --http --daemon     # Background
qmd mcp stop                # Stop daemon
```

## Tools

### query

Search with pre-expanded queries.

```json
{
  "searches": [
    { "type": "lex", "query": "keyword phrases" },
    { "type": "vec", "query": "natural language question" },
    { "type": "hyde", "query": "hypothetical answer passage..." }
  ],
  "limit": 10,
  "collections": ["optional-collection"],
  "minScore": 0.0
}
```

| Type | Method | Input |
|------|--------|-------|
| `lex` | BM25 | Keywords (2-5 terms) |
| `vec` | Vector | Question |
| `hyde` | Vector | Answer passage (50-100 words) |

### get

Retrieve document by path or `#docid`.

| Param | Type | Description |
|-------|------|-------------|
| `file` | string | File path, `#docid`, or `path:from:count` |
| `fromLine` | number? | Start line, 1-indexed |
| `maxLines` | number? | Limit returned lines |
| `lineNumbers` | bool? | Add line numbers |

### multi_get

Retrieve multiple documents.

| Param | Type | Description |
|-------|------|-------------|
| `pattern` | string | Glob or comma-separated list |
| `maxBytes` | number? | Skip large files (default 10KB) |
| `maxLines` | number? | Limit lines per file |

### status

Index health and collections. No params.

## Troubleshooting

- **Not starting**: `which qmd`, `qmd mcp` manually
- **No results**: `qmd collection list`, `qmd update`, `qmd embed`
- **Slow first search**: Normal, models loading (~3GB)
