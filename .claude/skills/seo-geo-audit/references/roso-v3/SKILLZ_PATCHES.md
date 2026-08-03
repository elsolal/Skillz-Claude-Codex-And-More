# Skillz-Claude integration patches

The vendored source starts from RosoAI SEO/GEO Squad V3.1.0 dated 2026-07-27.
Skillz-Claude applies the following distribution patches before rebuilding
`KIT_MANIFEST.json`:

- integrity scans evaluate paths relative to the kit so embedding below
  `.claude/skills/` does not hide every file;
- the HTML/PDF renderer only reads the report directory and bundled assets;
- the official-rule checker disables proxies, pins HTTPS connections to
  validated public IP addresses, and rejects private destinations;
- newly created projects keep `authorized_at` null until a real approver and
  timezone-aware timestamp are supplied;
- PDF fallback dependencies are installed in a virtual environment instead of
  bypassing PEP 668;
- missing PDF dependencies are reported as a delivery blocker instead of
  presenting internal Markdown previews as compliant client deliverables;
- security regression tests cover these integration guarantees.

These patches do not weaken the V3 evidence, scoring, QA or delivery contracts.
