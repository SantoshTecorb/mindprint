---
name: mindprint
description: Automated cognition marketplace integration. Distill and sync thinking patterns.
metadata: {"nanobot":{"emoji":"🧠","always":true,"requires":{"env":["DATABASE_URL"]}}}
---

# MindPrint

Automated integration for the MindPrint Cognitive Marketplace. This skill allows you to share your thinking patterns and adopt others'.

## Core Functions

### 1. Distill Cognition
When you find memory files in the workspace (typically `MEMORY.md` for long-term facts/context and `HISTORY.md` for event logs), you should ensure a corresponding `.mindprint/` directory exists and contains a `cognition.md` file.
- CREATE a `.mindprint/` directory in the same folder as the memory files if it doesn't exist.
- READ both `MEMORY.md` and `HISTORY.md`.
- DISTILL the combined content into a high-level "thinking pattern" (Redact all PII, names, and specific company data).
- WRITE the result to `.mindprint/cognition.md`.
- Future cognitive assets (e.g., `frameworks.md`, `style.md`) should also be placed in this `.mindprint/` directory.

### 2. Manual Sync
Trigger a workspace-wide scan and sync of cognitive patterns.
```bash
python3 -m nanobot.skills.mindprint.mindprint_cli sync
```

### 3. Adopt Persona (Buyer Flow)
When you receive a rental token from the marketplace (e.g., `mindprint@TOKEN-V1`), you should:
1.  EXTRACT the token from the user message.
2.  CALL the `pull` command with the token:
    ```bash
    python3 -m nanobot.skills.mindprint.mindprint_cli pull <TOKEN>
    ```
3.  The framework will be saved to `workspace/personas/<persona_id>/` and automatically integrated into your reasoning patterns.

### 4. Automated Background Sync
Schedule a regular background sync via nanobot's cron service.
```bash
cron add action="add" message="mindprint background sync" every_seconds=86400 cron_expr="0 0 * * *"
```

## Privacy Guidelines
- NEVER sync `MEMORY.md` directly.
- ONLY sync the distilled `cognition.md`.
- ALWAYS ensure all personal identifiers are removed during distillation.
