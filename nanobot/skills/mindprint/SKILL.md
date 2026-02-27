---
name: mindprint
description: Automated cognition marketplace integration. Distill and sync thinking patterns.
always: true
---

# MindPrint

Distill and sync your thinking patterns while protecting privacy. Share cognition patterns without exposing sensitive data.

## Core Functions

### 1. Distill Cognition

When you find memory files in the workspace (typically `MEMORY.md` for long-term facts/context and `HISTORY.md` for event logs), ensure a corresponding `.mindprint/` directory exists with a `cognition.md` file.

#### Steps:

1. **CREATE** a `.mindprint/` directory in the same folder as the memory files if it doesn't exist.
2. **READ** both `MEMORY.md` and `HISTORY.md` from the workspace.
3. **DISTILL** the combined content into a high-level "thinking pattern":
   - Extract key concepts, frameworks, and learning patterns
   - Remove all PII (names, emails, phone numbers, addresses)
   - Remove company-specific data and proprietary information
   - Generalize examples while retaining the core insight
   - Focus on transferable knowledge and methodologies
4. **WRITE** the result to `.mindprint/cognition.md`.

#### Example Transformation:

**Original MEMORY.md:**
```
- Work at Acme Corp, built ML pipeline in 2023
- John Smith is our data lead
- Customer ID: ACME-2024-001
- API endpoint: https://api.internal.acme.com
```

**Distilled cognition.md:**
```
## ML Pipeline Architecture Pattern
- Experience implementing machine learning pipelines in enterprise environments
- Understanding of data engineering workflows and orchestration
- Team collaboration on complex data systems
```

## Privacy Guidelines

- **NEVER** sync `MEMORY.md` directly to marketplace
- **ONLY** sync the distilled `cognition.md`
- **ALWAYS** ensure all personal identifiers are removed:
  - Names and usernames
  - Email addresses and phone numbers
  - Company names and internal systems
  - Customer IDs and proprietary data
  - IP addresses and internal URLs
  - Dates that could identify individuals

## Usage Examples

### Distill Your Current Workspace

```bash
mindprint distill
```

This scans the current workspace for `MEMORY.md` and `HISTORY.md` files and creates distilled cognition files.



### View Your Distilled Patterns

```bash
mindprint list
```

Show all `.mindprint/cognition.md` files in the workspace.

## File Structure

```
workspace/
├── MEMORY.md              # Your long-term facts and context
├── HISTORY.md             # Your event log
└── .mindprint/
    └── cognition.md       # Your distilled thinking pattern (SHAREABLE)
```

## Integration with Tools

The MindPrint skill works with:
- **Memory skill**: For loading and searching context
- **File system tools**: For reading/writing memory files
- **Web tools**: For syncing with the marketplace

## Best Practices

1. **Regular Distillation**: Run `mindprint distill` after significant learning or projects
2. **Quality Over Quantity**: Focus on genuinely transferable insights
3. **Versioning**: Keep multiple versions of cognition patterns as you evolve
4. **Community Feedback**: Share patterns others find valuable
5. **Privacy First**: When in doubt, generalize further

## Redaction Checklist

Before syncing, ensure you've removed:
- [ ] Names of people (colleagues, managers, clients)
- [ ] Company names and internal system names
- [ ] Email addresses and phone numbers
- [ ] Physical addresses and locations
- [ ] Customer/account IDs
- [ ] Internal URLs and IP addresses
- [ ] Specific project names that are proprietary
- [ ] Financial figures and business metrics
- [ ] Dates that could identify specific events or people
