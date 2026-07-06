# Healer

Auto-heals missing or invalid OKF frontmatter fields.

| Function | Returns | Description |
|----------|---------|-------------|
| `heal_frontmatter(content, filepath, vault_dir=None)` | `tuple[str, list[str]]` | Heal a single note's frontmatter. Returns (healed_content, list_of_changes). Empty changes list if nothing to heal. |
| `heal_vault(vault_dir, dry_run=True)` | `str` | Scan vault and heal all notes with missing/invalid frontmatter. Returns formatted report. Creates timestamped backups before live edits. |

## Fields healed

| Field | Heal strategy |
|-------|---------------|
| `type` | Inferred from parent P.A.R.A. folder (`01_Projects` → `Project`, `06_Daily_Logs` → `Daily Log`, etc.) |
| `title` | Converted from filename (kebab/snake to Title Case, date prefixes stripped) |
| `description` | Extracted from first non-header paragraph (max 150 chars) |
| `timestamp` | Added with current UTC time if missing |
| Type casing | Fixed if present but not in correct case (e.g. `project` → `Project`) |

## `HealVault` report

The `heal_vault()` function returns a formatted report with:

```
=== Frontmatter Heal Report ===
Vault: /path/to/vault
Mode: DRY RUN / LIVE
Notes healed: N

Changes:
  01_Projects/my-note.md:
    - Added missing type: Project
    - Added missing title: 'My Note'
```
