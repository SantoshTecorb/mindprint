---
name: mindprint
description: Automated cognition distillation and marketplace sync.
always: true
---

# MindPrint Skill

Distills workspace memory into a privacy-safe, shareable cognition profile.

This skill MUST NEVER expose raw memory files.

---

# Execution Contract

When invoked:

1. Detect `MEMORY.md` and/or `HISTORY.md` in the current workspace directory.
2. If neither file exists → EXIT with message: "No memory files found."
3. If at least one exists:
   - CREATE `.mindprint/` directory in same folder (if missing)
   - READ contents of both files
   - REDACT sensitive information
   - DISTILL cognition patterns
   - WRITE `.mindprint/cognition.md`
4. NEVER expose original memory content in output.
5. ONLY output path of generated file.

---

# Distillation Rules

The output MUST:

- Extract transferable thinking patterns
- Remove all personal identifiers
- Remove company and proprietary references
- Generalize specific examples
- Preserve methodology and cognitive approach
- Avoid referencing exact dates or traceable events

The output MUST NOT:

- Include any names
- Include email addresses
- Include phone numbers
- Include physical locations
- Include internal URLs or IP addresses
- Include company names
- Include unique identifiers
- Include financial or operational metrics
- Include raw memory content

---

# Redaction Requirements

The system MUST redact:

- Personal names
- Usernames
- Email addresses
- Phone numbers
- Company names
- Internal system names
- Customer IDs
- Account numbers
- API keys
- URLs
- IP addresses
- Precise dates
- Physical addresses
- Proprietary project names

If uncertain whether content is identifiable → REMOVE it.

---

# Output Format

File: `.mindprint/cognition.md`

Structure:

# 🧠 Cognitive Profile

## Core Thinking Patterns

- High-level transferable cognition patterns only
- Abstracted from repeated behaviors and problem-solving approaches
- Free of specific events, names, or traceable details

---

## Decision Approach

- How choices are evaluated
- Risk tolerance and validation style
- Analytical vs intuitive tendencies
- Short-term vs long-term orientation

---

## Learning Style

- How knowledge is acquired and processed
- Concept-first vs example-first learning
- Iterative experimentation vs structured study
- Preference for frameworks, comparisons, or implementation practice

---

## Execution Tendencies

- How ideas are implemented
- Planning depth before action
- Bias toward shipping vs refining
- Iteration speed and feedback loops

---

## Cognitive Strengths

- Observable repeatable strengths
- Pattern recognition ability
- Strategic thinking capacity
- Systems awareness
- Adaptability or optimization focus

---

## Generalized Experience Themes

- Broad categories of expertise
- Recurring domains of interest
- Types of problems frequently explored
- Environments or contexts commonly engaged with
---

# CLI Interface


mindprint distill

Behavior:
- Executes full distillation pipeline
- Returns:
  ✓ Cognition distilled → .mindprint/cognition.md

---

# Safety Model

- Raw memory files MUST NEVER be synced.
- Only `.mindprint/cognition.md` is shareable.
- If redaction fails → abort operation.
- Privacy takes priority over completeness.

---

# Integration Notes

Compatible with:
- Memory ingestion tools
- Filesystem operations
- Versioned cognition schemas

---

# Versioning

Each generated cognition file MUST include:

Cognition Model Version: 2.0

Future changes must increment version.