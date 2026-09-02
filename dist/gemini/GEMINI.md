# Skillz provider instructions

This extension contains generated D-EPCT workflow skills and Gemini-native commands.

## Runtime contract

1. When a command or task names a bundled skill, read that skill's complete `SKILL.md` before
   acting.
2. Treat the bundled skill as the workflow source of truth. This file only describes Gemini
   discovery and does not redefine workflow logic.
3. Preserve user-owned settings, credentials and files. Do not add permission-bypass flags.
4. Keep evidence labels narrow: generated structure is C1, native discovery is C2 and a behavioral
   run on a pinned runtime is C3.
5. If a required capability is marked pending or unsupported, report the limitation instead of
   simulating it.

The `commands/` directory contains Gemini TOML aliases. The `skills/` directory contains the shared
workflow implementations referenced by those aliases.
