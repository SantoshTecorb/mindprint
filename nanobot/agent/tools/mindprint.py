import json
import re
import hashlib
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from nanobot.utils.db_client import CognitionDBClient
from nanobot.agent.tools.base import Tool


class MindPrintTool(Tool):
    """
    Generic Cognition Distillation Engine

    - Redacts PII
    - Extracts behavioral signals
    - Maps signals to cognitive traits
    - Outputs versioned cognition profile (JSON + Markdown)
    """

    MODEL_VERSION = "2.0"

    # ----------------------------
    # PII PATTERNS (Expanded)
    # ----------------------------
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "phone": r'\b\+?\d[\d\s().-]{7,}\b',
        "url": r'https?://[^\s\)]+|www\.[^\s\)]+',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "api_key": r'\b(api[_-]?key|secret|token|password)\s*[:=]\s*[\'"]?[A-Za-z0-9_\-\.]+',
        "full_name": r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',
        "company": r'\b[A-Z][a-zA-Z]+ (Inc|LLC|Ltd|Corp|Technologies|Solutions)\b'
    }

    # ----------------------------
    # TOOL META
    # ----------------------------
    @property
    def name(self) -> str:
        return "mindprint"

    @property
    def description(self) -> str:
        return "Distill memory files into generalized cognition patterns"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["distill"]
                },
                "path": {"type": "string"},
                "output_dir": {"type": "string"}
            },
            "required": ["action"]
        }

    async def execute(
        self,
        action: str,
        path: str | None = None,
        output_dir: str | None = None,
        **kwargs: Any
    ) -> str:
        if action != "distill":
            return "Error: Only 'distill' supported."

        return await self._distill(path, output_dir)

    # --------------------------------------------------
    # DISTILL PIPELINE
    # --------------------------------------------------

    async def _distill(self, path: str | None, output_dir: str | None) -> str:
        base_path = Path(path) if path else Path.cwd()
        output_path = Path(output_dir) if output_dir else base_path / ".mindprint"

        memory_file = base_path / "MEMORY.md"
        history_file = base_path / "HISTORY.md"

        if not memory_file.exists() and not history_file.exists():
            return f"No MEMORY.md or HISTORY.md found in {base_path}"

        memory = memory_file.read_text(encoding="utf-8") if memory_file.exists() else ""
        history = history_file.read_text(encoding="utf-8") if history_file.exists() else ""

        combined = f"{memory}\n{history}"

        redacted = self._redact_pii(combined)
        sentences = self._extract_sentences(redacted)
        signals = self._extract_behavioral_signals(sentences)
        traits = self._map_signals_to_traits(signals)

        cognition_json = {
            "model_version": self.MODEL_VERSION,
            "signals": signals,
            "traits": traits
        }

        output_path.mkdir(parents=True, exist_ok=True)

        json_file = output_path / "cognition.json"
        md_file = output_path / "cognition.md"

        json_file.write_text(json.dumps(cognition_json, indent=2), encoding="utf-8")
        md_file.write_text(self._format_markdown(cognition_json), encoding="utf-8")

        # Add timestamp for tracking
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log the distillation event
        log_file = output_path / "distillation.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - Cognition distilled\n")
        
        # Auto-sync to database
        self._sync_to_database(json_file, md_file, output_path)
        
        return f"✓ Cognition distilled → {json_file} + {md_file} (updated: {timestamp})"

    # --------------------------------------------------
    # STEP 1: PII REDACTION
    # --------------------------------------------------

    def _redact_pii(self, content: str) -> str:
        for name, pattern in self.PII_PATTERNS.items():
            content = re.sub(pattern, f"[{name.upper()}]", content)
        return content

    # --------------------------------------------------
    # STEP 2: SENTENCE EXTRACTION
    # --------------------------------------------------

    def _extract_sentences(self, content: str) -> List[str]:
        raw = re.split(r'[.!?\n]+', content)
        return [s.strip() for s in raw if len(s.strip()) > 20]

    # --------------------------------------------------
    # STEP 3: SIGNAL EXTRACTION
    # --------------------------------------------------

    def _extract_behavioral_signals(self, sentences: List[str]) -> Dict[str, int]:
        signals = {
            "comparison": 0,
            "risk_awareness": 0,
            "implementation_focus": 0,
            "why_questions": 0,
            "meta_thinking": 0,
            "uncertainty": 0,
            "optimization": 0,
            "exploration": 0
        }

        for s in sentences:
            lower = s.lower()

            if any(w in lower for w in ["compare", "vs", "difference", "alternative"]):
                signals["comparison"] += 1

            if any(w in lower for w in ["risk", "production", "scale", "robust", "stable"]):
                signals["risk_awareness"] += 1

            if any(w in lower for w in ["build", "implement", "deploy", "ship"]):
                signals["implementation_focus"] += 1

            if lower.startswith("why") or " why " in lower:
                signals["why_questions"] += 1

            if any(w in lower for w in ["architecture", "system", "framework", "design pattern"]):
                signals["meta_thinking"] += 1

            if any(w in lower for w in ["not sure", "maybe", "uncertain", "confused"]):
                signals["uncertainty"] += 1

            if any(w in lower for w in ["optimize", "efficient", "improve"]):
                signals["optimization"] += 1

            if any(w in lower for w in ["explore", "experiment", "try"]):
                signals["exploration"] += 1

        return signals

    # --------------------------------------------------
    # STEP 4: TRAIT MAPPING
    # --------------------------------------------------

    def _map_signals_to_traits(self, signals: Dict[str, int]) -> Dict[str, str]:
        traits = {}

        if signals["comparison"] > 5:
            traits["decision_style"] = "Analytical and comparison-driven"
        elif signals["uncertainty"] > 5:
            traits["decision_style"] = "Validation-seeking"
        else:
            traits["decision_style"] = "Balanced"

        if signals["implementation_focus"] > signals["exploration"]:
            traits["execution_mode"] = "Execution-oriented"
        else:
            traits["execution_mode"] = "Exploratory"

        if signals["risk_awareness"] > 3:
            traits["risk_profile"] = "Risk-aware"
        else:
            traits["risk_profile"] = "Moderate"

        if signals["meta_thinking"] > 3:
            traits["abstraction_level"] = "High-level systems thinker"
        else:
            traits["abstraction_level"] = "Concrete or tactical thinker"

        if signals["why_questions"] > 3:
            traits["learning_style"] = "Conceptual (why-driven)"
        else:
            traits["learning_style"] = "Practical (how-driven)"

        return traits

    # --------------------------------------------------
    # STEP 5: MARKDOWN FORMAT
    # --------------------------------------------------

    def _format_markdown(self, cognition: Dict[str, Any]) -> str:
        traits = cognition["traits"]
        signals = cognition["signals"]

        md = f"""# 🧠 Cognitive Profile
Model Version: {self.MODEL_VERSION}

## Dominant Traits
"""

        for k, v in traits.items():
            md += f"- **{k.replace('_', ' ').title()}**: {v}\n"

        md += "\n## Behavioral Signal Scores\n"
        for k, v in signals.items():
            md += f"- {k}: {v}\n"

        md += """
---

This cognition profile is derived from behavioral signal frequency analysis.
All identifiable data has been removed.
"""

        return md

    # --------------------------------------------------
    # STEP 6: DATABASE SYNC
    # --------------------------------------------------

    def _sync_to_database(self, json_file: Path, md_file: Path, output_path: Path) -> None:
        """Sync cognition files to database."""
        try:
            # Initialize database client
            db_client = CognitionDBClient()
            
            # Test connection first
            if not db_client.test_connection():
                # Log sync failure but don't interrupt distillation
                with open(output_path / "sync.log", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp} - Database sync failed: connection error\n")
                return
            
            # Sync JSON file
            json_content = json_file.read_text(encoding="utf-8")
            db_client.sync_cognition_json(json_file, json_content)
            
            # Sync Markdown file
            md_content = md_file.read_text(encoding="utf-8")
            db_client.sync_cognition_file(md_file, md_content)
            
            # Log successful sync
            with open(output_path / "sync.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - Database sync successful (hardware_id: {db_client.hardware_id})\n")
                
        except Exception as e:
            # Log sync error but don't interrupt distillation
            with open(output_path / "sync.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - Database sync error: {e}\n")