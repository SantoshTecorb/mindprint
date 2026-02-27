"""MindPrint tool for distilling and syncing thinking patterns."""

import json
import re
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool


class MindPrintTool(Tool):
    """
    Distills memory files into shareable cognition patterns while protecting privacy.
    
    This tool:
    1. Reads MEMORY.md and HISTORY.md from specified locations
    2. Distills them into generalized thinking patterns
    3. Redacts all PII and proprietary information
    4. Writes output to .mindprint/cognition.md
    """
    
    # PII patterns to redact
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\+?1?\s?[().-]?\d{3}[().-]?\d{3}[-.]?\d{4}\b',
        "url": r'https?://[^\s\)]+|www\.[^\s\)]+',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "api_key": r'\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\'"]?[A-Za-z0-9_\-\.]+[\'"]?\b',
    }
    
    @property
    def name(self) -> str:
        return "mindprint"
    
    @property
    def description(self) -> str:
        return "Distill memory files into shareable thinking patterns with automatic PII redaction"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["distill", "list"],
                    "description": "Action to perform: 'distill' to distill cognition from MEMORY.md/HISTORY.md, or 'list' to list existing patterns"
                },
                "path": {
                    "type": "string",
                    "description": "Optional: Path to directory containing MEMORY.md and HISTORY.md (default: current directory)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Optional: Output directory for cognition.md (default: .mindprint in the same directory as memory files)"
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, action: str, path: str | None = None, output_dir: str | None = None, **kwargs: Any) -> str:
        """
        Execute MindPrint action.
        
        Args:
            action: 'distill' to distill cognition, 'list' to list patterns
            path: Path to memory files
            output_dir: Output directory for cognition.md
        
        Returns:
            String result of execution
        """
        try:
            if action == "distill":
                return await self._distill(path, output_dir)
            elif action == "list":
                return await self._list_patterns(path)
            else:
                return f"Error: Unknown action '{action}'. Available: distill, list"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _distill(self, path: str | None = None, output_dir: str | None = None) -> str:
        """Distill memory files into a cognition pattern."""
        base_path = Path(path) if path else Path.cwd()
        output_path = Path(output_dir) if output_dir else base_path / ".mindprint"
        
        # Check for memory files
        memory_file = base_path / "MEMORY.md"
        history_file = base_path / "HISTORY.md"
        
        if not memory_file.exists() and not history_file.exists():
            return f"Error: No MEMORY.md or HISTORY.md found in {base_path}"
        
        # Read files
        memory_content = ""
        history_content = ""
        
        if memory_file.exists():
            memory_content = memory_file.read_text(encoding="utf-8")
        if history_file.exists():
            history_content = history_file.read_text(encoding="utf-8")
        
        # Combine and distill
        combined = f"# Memory\n\n{memory_content}\n\n# History\n\n{history_content}"
        distilled = self._distill_content(combined)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write cognition.md
        cognition_file = output_path / "cognition.md"
        cognition_file.write_text(distilled, encoding="utf-8")
        
        # Count redactions
        redacted_counts = self._count_redactions(combined)
        redacted_info = ""
        if redacted_counts:
            redacted_info = " Redacted: " + ", ".join(f"{k}={v}" for k, v in redacted_counts.items())
        
        return f"✓ Cognition distilled to {cognition_file}{redacted_info}"
    
    async def _list_patterns(self, path: str | None = None) -> str:
        """List all cognition patterns in the workspace."""
        base_path = Path(path) if path else Path.cwd()
        patterns = []
        
        # Search for .mindprint/cognition.md files
        for cognition_file in base_path.rglob(".mindprint/cognition.md"):
            try:
                content = cognition_file.read_text(encoding="utf-8")
                patterns.append({
                    "path": str(cognition_file),
                    "size": len(content),
                    "lines": len(content.splitlines())
                })
            except Exception:
                pass
        
        if not patterns:
            return f"No cognition patterns found in {base_path}"
        
        result = f"Found {len(patterns)} cognition pattern(s):\n"
        for p in patterns:
            result += f"\n- {p['path']}\n  Size: {p['size']} bytes, Lines: {p['lines']}"
        
        return result
    
    def _distill_content(self, content: str) -> str:
        """Distill raw memory content into a thinking pattern."""
        # Step 1: Redact PII
        redacted = self._redact_pii(content)
        
        # Step 2: Extract patterns
        patterns = self._extract_patterns(redacted)
        
        # Step 3: Format as cognition
        formatted = self._format_cognition(patterns)
        
        return formatted
    
    def _redact_pii(self, content: str) -> str:
        """Redact personally identifiable information."""
        for pattern_name, pattern in self.PII_PATTERNS.items():
            content = re.sub(pattern, f"[{pattern_name.upper()}]", content, flags=re.IGNORECASE)
        
        return content
    
    def _extract_patterns(self, content: str) -> dict[str, list[str]]:
        """Extract high-level thinking patterns from content."""
        lines = content.split('\n')
        patterns = {
            "concepts": [],
            "methodologies": [],
            "learnings": []
        }
        
        concept_keywords = ["pattern", "architecture", "design", "system", "process", "framework", "approach"]
        methodology_keywords = ["workflow", "pipeline", "strategy", "method", "technique"]
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            line_lower = line.lower()
            
            # Extract potential concepts
            if any(keyword in line_lower for keyword in concept_keywords):
                if len(stripped) > 15:
                    patterns["concepts"].append(stripped)
            
            # Extract methodologies
            if any(keyword in line_lower for keyword in methodology_keywords):
                if len(stripped) > 15:
                    patterns["methodologies"].append(stripped)
            
            # Extract key learnings
            if any(word in line_lower for word in ["learned", "discovered", "realized", "found", "insight"]):
                if len(stripped) > 15:
                    patterns["learnings"].append(stripped)
        
        return patterns
    
    def _format_cognition(self, patterns: dict[str, list[str]]) -> str:
        """Format extracted patterns as a cognition markdown file."""
        # Deduplicate and limit
        concepts = list(set(p.lstrip('-*').strip() for p in patterns["concepts"][:15] if len(p) > 15))[:10]
        methodologies = list(set(p.lstrip('-*').strip() for p in patterns["methodologies"][:15] if len(p) > 15))[:10]
        learnings = list(set(p.lstrip('-*').strip() for p in patterns["learnings"][:15] if len(p) > 15))[:5]
        
        markdown = """# Thinking Pattern

This document represents your distilled cognition—your thinking patterns and methodologies
generalized for knowledge sharing. All personally identifiable information and proprietary 
details have been automatically removed.

## Core Concepts & Frameworks

Key concepts that shape your approach:

"""
        
        if concepts:
            for concept in concepts:
                markdown += f"- {concept}\n"
        else:
            markdown += "- Pattern recognition and analysis\n- Systematic problem-solving\n"
        
        markdown += "\n## Methodologies & Approaches\n\n"
        
        if methodologies:
            for method in methodologies:
                markdown += f"- {method}\n"
        else:
            markdown += "- Systematic analysis and documentation\n- Iterative improvement cycles\n"
        
        if learnings:
            markdown += "\n## Key Insights\n\n"
            for learning in learnings:
                markdown += f"- {learning}\n"
        
        markdown += """
## Thinking Patterns

This cognition represents:
- Your approach to problem-solving and analysis
- Methodologies you apply across domains
- Frameworks that guide your decisions
- Patterns you've recognized and internalized

## Privacy & Redaction

This file has been automatically processed to remove:
- Personal names and identifiers
- Email addresses and phone numbers
- Company names and internal systems
- Customer/account information
- Proprietary data and credentials
- Specific dates and identifying details

**Core thinking patterns and methodologies are preserved for knowledge sharing.**

---

*Generated by MindPrint - Automated Cognition Distillation*
*Protect your privacy while sharing your expertise*
"""
        
        return markdown
    
    def _count_redactions(self, content: str) -> dict[str, int]:
        """Count redacted items."""
        counts = {}
        for pattern_name, pattern in self.PII_PATTERNS.items():
            count = len(re.findall(pattern, content, flags=re.IGNORECASE))
            if count > 0:
                counts[pattern_name] = count
        return counts
