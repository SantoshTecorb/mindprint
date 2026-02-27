# MindPrint Skill Documentation

## Overview

MindPrint is a built-in skill that enables you to distill your thinking patterns from memory files while automatically protecting privacy through PII redaction. It transforms your `MEMORY.md` and `HISTORY.md` files into shareable `cognition.md` files that preserve your methodologies and insights while removing sensitive information.

## Why MindPrint?

### Problem
- **Privacy Risk**: Sharing knowledge often requires sharing memory files that contain sensitive information
- **Manual Redaction**: Manual removal of PII is tedious and error-prone
- **Knowledge Hoarding**: Without a safe way to share, valuable thinking patterns stay locked away

### Solution
MindPrint automatically:
1. **Redacts PII** - Removes emails, phone numbers, URLs, IP addresses, API keys, and customer IDs
2. **Extracts Patterns** - Identifies core concepts, methodologies, and insights
3. **Formats Knowledge** - Creates structured, shareable cognition files
4. **Preserves Intent** - Maintains the essence of your thinking while removing specifics

## How It Works

### Two-Layer Memory System

Your workspace has:
```
workspace/
├── MEMORY.md           # Long-term facts and context (private)
├── HISTORY.md          # Event logs and learnings (private)
└── .mindprint/
    └── cognition.md    # Distilled, shareable thinking pattern
```

### Processing Pipeline

```
MEMORY.md + HISTORY.md
        ↓
   [Combine]
        ↓
   [Redact PII]
        ↓
   [Extract Patterns]
        ↓
   [Format as Cognition]
        ↓
  cognition.md (SHAREABLE)
```

## Tool Usage

The MindPrint tool provides two actions:

### 1. Distill Action

**Purpose**: Transform memory files into a cognition pattern

```
mindprint(action="distill", path=<optional>, output_dir=<optional>)
```

**Parameters**:
- `action` (required): `"distill"`
- `path` (optional): Directory containing MEMORY.md and HISTORY.md. Default: current directory
- `output_dir` (optional): Where to save cognition.md. Default: `.mindprint` in the memory directory

**Returns**: Success message with redaction counts

**Example**:
```
mindprint(action="distill", path="/workspace", output_dir="/workspace/.mindprint")
```

### 2. List Action

**Purpose**: Find all existing cognition patterns in workspace

```
mindprint(action="list", path=<optional>)
```

**Parameters**:
- `action` (required): `"list"`
- `path` (optional): Directory to search. Default: current directory

**Returns**: List of found cognition.md files with metadata

**Example**:
```
mindprint(action="list", path="/workspace")
```

## Privacy Redaction

### Automatically Detected & Redacted

MindPrint scans for and removes:

1. **Email Addresses**
   - Pattern: `user@domain.com`
   - Examples: `john.doe@company.com`, `contact@email.io`

2. **Phone Numbers**
   - Pattern: `(555) 123-4567`, `555-123-4567`, `+1-555-123-4567`
   - Examples: `(555) 123-4567`, `555.123.4567`

3. **URLs & Internal Domains**
   - Pattern: `https://...`, `http://...`, `www.site.com`
   - Examples: `https://internal-api.company.com`, `api.example.com`

4. **IP Addresses**
   - Pattern: `XXX.XXX.XXX.XXX`
   - Examples: `192.168.1.100`, `10.0.0.5`

5. **API Keys & Secrets**
   - Pattern: `api_key: "..."`, `secret: "..."`
   - Examples: `sk_test_123456`, `SECRET_TOKEN_ABCD`

6. **Customer/Account IDs**
   - Pattern: `ABBR-YYYY-ZZZ`
   - Examples: `ACME-2024-001`, `CUST-2023-042`

### Redaction Process

Found items are replaced with placeholders like:
- `[EMAIL]` for email addresses
- `[PHONE]` for phone numbers
- `[URL]` for URLs
- `[IP_ADDRESS]` for IP addresses
- `[API_KEY]` for secrets
- `[CUSTOMER_ID]` for account IDs

### Manual Review

Always review the generated `cognition.md` file before sharing. The redaction is automated but not perfect. Look for:

- Specific names that weren't caught
- Internal product/project names
- Unique identifiers (product codes, order numbers)
- Business metrics or sensitive dates
- Acronyms that reveal company specifics

## Examples

### Example 1: Team Learning Pattern

**Original MEMORY.md:**
```markdown
# Database Optimization

## Team Members
- Sarah Chen (sarah.chen@acme.com) - Lead
- Marcus Johnson (marcus@company.io) - DBA

## What We Learned
Built a database query optimization framework for Postgres.
Used explain plans and statistics to identify bottlenecks.
Implemented connection pooling to reduce overhead.

## Metrics
- Reduced query time by 60% on customer reports
- Customer ID: ACME-2024-156
- Internal database: db.internal.acme.com
```

**Distilled cognition.md:**
```markdown
# Thinking Pattern

## Core Concepts & Frameworks

- Database query optimization techniques
- Query plan analysis and statistics
- Connection pooling patterns

## Methodologies & Approaches

- Using database explain plans for performance debugging
- Statistical analysis of query execution
- Connection lifecycle optimization

## Key Insights

- Query optimization can significantly reduce latency
- Systematic analysis is key to identifying bottlenecks
```

All names, emails, internal systems, and customer IDs are automatically removed.

### Example 2: Technical Decision Pattern

**Original HISTORY.md:**
```markdown
## 2024-02-15

Evaluated deployment platforms for microservices.
Compared: Kubernetes vs ECS vs Nomad
Internal infra: https://deploy.company-internal.com

Winner: Kubernetes for flexibility and ecosystem
Contact: devops@company.email

API credentials stored at sk_prod_abc123xyz789
```

**Distilled cognition.md:**
```markdown
## Methodologies & Approaches

- Systematic evaluation of deployment platforms
- Technology comparison and selection process
- Microservices deployment architecture decisions

## Key Insights

- Container orchestration platform selection depends on ecosystem needs
- Flexibility and community support are important factors
```

URLs, credentials, emails, and implementation details are automatically redacted.

## Best Practices

### 1. Regular Distillation

Distill after major learnings or projects:
```
mindprint(action="distill")  # Run regularly
```

### 2. Iterative Refinement

- First run generates base cognition
- Review and enhance MEMORY.md with better descriptions
- Run again for improved distillation
- Process: Enhance → Distill → Share

### 3. Quality Over Quantity

Focus on:
- **Transferable Knowledge**: Patterns others can apply
- **Generalizable Insights**: Not specific to your company
- **Methodologies**: How you think and solve problems

Avoid:
- Trivial observations
- Company-specific implementations
- Proprietary algorithms or data

### 4. Privacy-First Approach

When in doubt:
- Generalize further
- Remove more specifics
- Err on the side of caution

Use this checklist before sharing:
- [ ] No personal names
- [ ] No email addresses
- [ ] No phone numbers
- [ ] No internal URLs or domains
- [ ] No company names
- [ ] No customer/account information
- [ ] No API keys or credentials
- [ ] No specific dates that identify events
- [ ] No proprietary product names

### 5. Versioning

Keep multiple versions as you evolve:
```
.mindprint/
├── cognition.md
├── cognition-v1-basic.md
├── cognition-v2-advanced.md
└── cognition-production-patterns.md
```

## Integration with Nanobot

MindPrint is built as a core tool in the Nanobot agent. The agent can:

1. **Automatically suggest distillation** when memory files grow large
2. **Trigger distillation** as part of memory consolidation
3. **Help refine patterns** by discussing insights
4. **Validate privacy** before sharing

### Usage in Nanobot Context

The agent can use MindPrint:

```python
# Distill at end of session
result = await agent.tools.execute("mindprint", {
    "action": "distill",
    "path": str(workspace)
})

# List existing patterns
patterns = await agent.tools.execute("mindprint", {
    "action": "list"
})
```

## Limitations & Known Issues

1. **Pattern Detection**: Extraction is heuristic-based, not perfect
2. **False Positives**: Some legitimate text may be redacted
3. **False Negatives**: Some PII may slip through (always review)
4. **Context Loss**: Distillation may lose some specific examples
5. **Redaction Reversibility**: Placeholders don't preserve original structure

## Troubleshooting

### No MEMORY.md or HISTORY.md Found

**Error**: `Error: No MEMORY.md or HISTORY.md found in {path}`

**Solution**: Ensure memory files exist in the specified directory
```bash
ls -la MEMORY.md HISTORY.md
```

### Incomplete Redaction

**Issue**: Some PII remains in cognition.md

**Solution**:
1. Manually review and edit cognition.md
2. Or enhance MEMORY.md/HISTORY.md with safer descriptions
3. Run distill again

### Too Much Content Removed

**Issue**: Important patterns are redacted

**Solution**:
1. Review PII detection rules
2. Rephrase memory content to avoid pattern matching
3. Manually enhance the resulting cognition.md

## File Structure Reference

### MEMORY.md (Private)
```markdown
# Long-Term Facts

## Context
- Project details
- Team information
- System architecture

## Preferences
- Technical choices
- Approaches used
- Lessons learned

## Relationships
- Key contacts
- Dependencies
- Team structure
```

### HISTORY.md (Private)
```markdown
# Event Log

## [Date]
- What happened
- What was learned
- How it was solved

## [Date]
- Decision made
- Methodology used
- Outcome
```

### .mindprint/cognition.md (Shareable)
```markdown
# Thinking Pattern

## Core Concepts & Frameworks
- Distilled patterns
- Key frameworks
- Essential methodologies

## Methodologies & Approaches
- How you solve problems
- Techniques you use
- Strategies employed

## Key Insights
- Transferable learnings
- Best practices discovered
- Generalizable knowledge
```

## See Also

- **Memory Skill**: Documentation on the two-layer memory system
- **Agent Context**: How skills are loaded and used
- **Privacy Guidelines**: Nanobot's approach to data protection

## Questions?

MindPrint is designed to be privacy-first and transparent. If you have questions about:
- What's being redacted: Check the redaction summary in output
- Privacy concerns: Always manually review before sharing
- Enhancement ideas: Contribute to the skill repository
