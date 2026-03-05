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

        # Generate comprehensive cognitive architecture
        cognition_data = self._generate_cognitive_architecture(sentences, signals, traits)

        output_path.mkdir(parents=True, exist_ok=True)

        # Generate the 10 cognitive files
        generated_files = []
        for file_name, content in cognition_data.items():
            file_path = output_path / file_name
            file_path.write_text(content, encoding="utf-8")
            generated_files.append(file_path)

        # Add timestamp for tracking
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log the distillation event
        log_file = output_path / "distillation.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - Cognitive architecture distilled\n")
        
        # Auto-sync to database
        self._sync_cognitive_architecture(generated_files, output_path)
        
        file_list = ", ".join([f.name for f in generated_files])
        return f"✓ Cognitive architecture distilled → {file_list} (updated: {timestamp})"

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
                    f.write(f"{timestamp} - Database sync failed: connection error (Tip: nanobot mindprint server start)\n")
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

    # --------------------------------------------------
    # STEP 7: COGNITIVE ARCHITECTURE GENERATION
    # --------------------------------------------------

    def _generate_cognitive_architecture(self, sentences: List[str], signals: Dict[str, int], traits: Dict[str, str]) -> Dict[str, str]:
        """Generate the 10-file cognitive architecture."""
        
        # Analyze content patterns
        problem_patterns = self._extract_problem_patterns(sentences)
        decision_patterns = self._extract_decision_patterns(sentences)
        value_patterns = self._extract_value_patterns(sentences)
        execution_patterns = self._extract_execution_patterns(sentences)
        meta_patterns = self._extract_meta_patterns(sentences)
        goal_patterns = self._extract_goal_patterns(sentences)
        knowledge_patterns = self._extract_knowledge_patterns(sentences)
        systems_patterns = self._extract_systems_patterns(sentences)
        stability_patterns = self._extract_stability_patterns(sentences)
        communication_patterns = self._extract_communication_patterns(sentences)

        return {
            "01_cognitive_blueprint.md": self._format_cognitive_blueprint(signals, traits, problem_patterns),
            "02_value_optimization_map.md": self._format_value_optimization(value_patterns, traits),
            "03_decision_tree_system.md": self._format_decision_tree_system(decision_patterns, signals),
            "04_meta_cognition_system.md": self._format_meta_cognition_system(meta_patterns, traits),
            "05_execution_operating_system.md": self._format_execution_operating_system(execution_patterns, signals),
            "06_goal_planning_architecture.md": self._format_goal_planning_architecture(goal_patterns, traits),
            "07_knowledge_framework.md": self._format_knowledge_framework(knowledge_patterns, signals),
            "08_systems_and_long_horizon_models.md": self._format_systems_models(systems_patterns, traits),
            "09_self_stability_profile.md": self._format_self_stability_profile(stability_patterns, signals),
            "10_communication_layer.md": self._format_communication_layer(communication_patterns, traits)
        }

    def _sync_cognitive_architecture(self, files: List[Path], output_path: Path) -> None:
        """Sync all cognitive architecture files to database."""
        try:
            db_client = CognitionDBClient()
            
            if not db_client.test_connection():
                with open(output_path / "sync.log", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp} - Database sync failed: connection error\n")
                return
            
            for file_path in files:
                content = file_path.read_text(encoding="utf-8")
                db_client.sync_cognition_file(file_path, content)
            
            with open(output_path / "sync.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - Cognitive architecture sync successful (hardware_id: {db_client.hardware_id})\n")
                
        except Exception as e:
            with open(output_path / "sync.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - Database sync error: {e}\n")

    # Pattern extraction methods
    def _extract_problem_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "problem_types": [],
            "categorization_rules": [],
            "signal_noise_filters": [],
            "analytical_flow": []
        }
        
        # Extract problem categorization patterns
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['problem', 'issue', 'challenge', 'obstacle']):
                patterns["problem_types"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_decision_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "decision_structures": [],
            "historical_choices": [],
            "risk_models": [],
            "tradeoff_patterns": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['decide', 'choice', 'option', 'tradeoff', 'risk']):
                patterns["decision_structures"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_value_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "optimization_targets": [],
            "tradeoff_hierarchy": [],
            "non_negotiables": [],
            "utility_weights": {}
        }
        
        # Extract value optimization patterns
        value_keywords = ['money', 'speed', 'control', 'optionality', 'efficiency', 'quality']
        for sentence in sentences:
            for value in value_keywords:
                if value in sentence.lower():
                    patterns["optimization_targets"].append(value)
        
        return patterns

    def _extract_execution_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "action_conversion": [],
            "tool_leverage": [],
            "delegation_rules": [],
            "resource_prioritization": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['execute', 'implement', 'build', 'create', 'tool']):
                patterns["action_conversion"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_meta_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "bias_awareness": [],
            "confidence_scaling": [],
            "error_detection": [],
            "self_correction": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['bias', 'confidence', 'error', 'mistake', 'learning']):
                patterns["bias_awareness"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_goal_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "goal_decomposition": [],
            "planning_method": [],
            "priority_logic": [],
            "progress_tracking": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['goal', 'plan', 'priority', 'progress', 'achieve']):
                patterns["goal_decomposition"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_knowledge_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "domain_depth": {},
            "core_models": [],
            "key_entities": [],
            "cross_domain_links": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['know', 'understand', 'model', 'framework', 'system']):
                patterns["core_models"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_systems_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "systems_thinking": [],
            "long_term_simulation": [],
            "second_order_reasoning": [],
            "multi_variable_modeling": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['system', 'long term', 'future', 'impact', 'consequence']):
                patterns["systems_thinking"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_stability_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "strength_zones": [],
            "break_points": [],
            "recurring_mistakes": [],
            "identity_constraints": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['strength', 'weakness', 'limitation', 'mistake', 'fail']):
                patterns["strength_zones"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    def _extract_communication_patterns(self, sentences: List[str]) -> Dict[str, Any]:
        patterns = {
            "output_style": [],
            "compression_level": [],
            "audience_switching": [],
            "formatting_bias": []
        }
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['communicate', 'explain', 'format', 'style', 'audience']):
                patterns["output_style"].append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        
        return patterns

    # Formatting methods for each cognitive file
    def _format_cognitive_blueprint(self, signals: Dict[str, int], traits: Dict[str, str], patterns: Dict[str, Any]) -> str:
        return f"""# 🧠 Cognitive Blueprint

*Core reasoning structure, problem categorization, signal vs noise filtering, and analytical flow*

## Core Reasoning Structure

### Decision Style: {traits.get('decision_style', 'Unknown')}
### Execution Mode: {traits.get('execution_mode', 'Unknown')}
### Risk Profile: {traits.get('risk_profile', 'Unknown')}
### Abstraction Level: {traits.get('abstraction_level', 'Unknown')}
### Learning Style: {traits.get('learning_style', 'Unknown')}

## Problem Categorization Rules

{chr(10).join(f"- {ptype}" for ptype in patterns['problem_types'][:5])}

## Signal vs Noise Filtering Rules

### Behavioral Signal Analysis
{chr(10).join(f"- **{signal}**: {count}" for signal, count in signals.items() if count > 0)}

### Noise Reduction Patterns
- Remove redundant information
- Filter out emotional responses
- Focus on actionable insights
- Prioritize data-driven observations

## Default Analytical Flow

1. **Problem Identification** - Recognize patterns and categorize issues
2. **Signal Extraction** - Identify key behavioral indicators
3. **Trait Mapping** - Connect signals to cognitive patterns
4. **Solution Generation** - Apply established reasoning frameworks
5. **Validation** - Cross-check with historical outcomes

---

*This blueprint encodes the fundamental logic engine for cognitive processing.*
"""

    def _format_value_optimization(self, patterns: Dict[str, Any], traits: Dict[str, str]) -> str:
        return f"""# ⚖️ Value Optimization Map

*What is being optimized, tradeoff hierarchy, non-negotiables, and utility weighting*

## Primary Optimization Targets

{chr(10).join(f"- {target}" for target in patterns['optimization_targets'][:5] if target)}

## Tradeoff Hierarchy

### 1. Core Values (Non-negotiable)
- **Quality**: Maintain high standards
- **Integrity**: Consistent application of principles
- **Learning**: Continuous improvement focus

### 2. Secondary Values (Flexible)
- **Speed**: Balance with thoroughness
- **Efficiency**: Optimize for resource usage
- **Control**: Maintain appropriate oversight

### 3. Contextual Values (Situational)
- **Optionality**: Preserve future choices
- **Cost**: Consider resource constraints
- **Convenience**: Balance with effectiveness

## Utility Weighting Model

Based on behavioral analysis:
- **Implementation Focus**: {traits.get('execution_mode', 'Unknown')}
- **Risk Tolerance**: {traits.get('risk_profile', 'Unknown')}
- **Learning Priority**: {traits.get('learning_style', 'Unknown')}

## Decision Direction Rules

1. **Quality First** - Never compromise core standards
2. **Learning Integration** - Extract maximum insight from each action
3. **Resource Efficiency** - Optimize for sustainable execution
4. **Long-term Value** - Prioritize durable solutions over quick fixes

---

*This map determines the fundamental direction of all decision-making.*
"""

    def _format_decision_tree_system(self, patterns: Dict[str, Any], signals: Dict[str, int]) -> str:
        return f"""# 🌳 Decision Tree System

*Recurring decision structures, historical choices, risk models, and tradeoff patterns*

## Recurring Decision Structures

{chr(10).join(f"- {structure}" for structure in patterns['decision_structures'][:5])}

## Historical Choice Patterns

### Decision Framework
1. **Problem Analysis** - Break down complex issues
2. **Option Generation** - Create multiple pathways
3. **Risk Assessment** - Evaluate potential outcomes
4. **Tradeoff Analysis** - Weigh competing priorities
5. **Action Selection** - Choose optimal path
6. **Outcome Review** - Learn from results

## Risk Models

### Risk Tolerance: {signals.get('risk_awareness', 0)}/10
- **Low Risk (0-3)**: Conservative approach, proven methods
- **Medium Risk (4-6)**: Calculated risks with mitigation
- **High Risk (7-10)**: Bold moves with high potential

### Risk Assessment Framework
- **Probability Assessment** - Likelihood of outcomes
- **Impact Analysis** - Magnitude of consequences
- **Mitigation Planning** - Reduce downside exposure
- **Contingency Preparation** - Backup strategies

## Tradeoff Patterns

### Common Tradeoffs
- **Speed vs Quality** - Balance thoroughness with urgency
- **Cost vs Features** - Resource allocation decisions
- **Control vs Autonomy** - Delegation and oversight balance
- **Short-term vs Long-term** - Temporal priority setting

---

*This system encodes behavioral intelligence through pattern recognition and structured choice.*
"""

    def _format_meta_cognition_system(self, patterns: Dict[str, Any], traits: Dict[str, str]) -> str:
        return f"""# 🎯 Meta-Cognition System

*Bias awareness, confidence scaling, error detection, and self-correction mechanisms*

## Bias Awareness Map

### Identified Bias Patterns
{chr(10).join(f"- {bias}" for bias in patterns['bias_awareness'][:5])}

### Common Cognitive Biases to Monitor
- **Confirmation Bias** - Seek disconfirming evidence
- **Anchoring Bias** - Question initial assumptions
- **Availability Bias** - Consider less obvious options
- **Overconfidence Bias** - Calibrate confidence levels

## Confidence Scaling Rules

### Confidence Levels
- **0-2 (Low)**: Seek more information, postpone decisions
- **3-5 (Medium)**: Proceed with caution, monitor closely
- **6-8 (High)**: Act decisively, validate assumptions
- **9-10 (Very High)**: Execute boldly, maintain oversight

### Meta-Thinking Score: {traits.get('abstraction_level', 'Unknown')}

## Error Detection Triggers

### Red Flags
- **Inconsistent Logic** - Check reasoning chains
- **Emotional Responses** - Separate feelings from facts
- **Rapid Conclusions** - Slow down for complex issues
- **Expertise Overreach** - Stay within knowledge boundaries

## Self-Correction Mechanisms

### Correction Process
1. **Recognition** - Identify potential errors
2. **Analysis** - Understand root causes
3. **Adjustment** - Modify approach
4. **Validation** - Test corrections
5. **Documentation** - Record learning

### Learning Integration
- **Pattern Recognition** - Identify recurring mistakes
- **Process Improvement** - Refine decision frameworks
- **Knowledge Updates** - Incorporate new insights

---

*This system ensures reliability under uncertainty through continuous self-monitoring.*
"""

    def _format_execution_operating_system(self, patterns: Dict[str, Any], signals: Dict[str, int]) -> str:
        return f"""# ⚡ Execution Operating System

*Idea-to-action conversion, tool leverage, delegation rules, and resource prioritization*

## Action Conversion Framework

### Implementation Focus: {signals.get('implementation_focus', 0)}/10

{chr(10).join(f"- {action}" for action in patterns['action_conversion'][:5])}

### Execution Pipeline
1. **Idea Capture** - Document concepts immediately
2. **Feasibility Assessment** - Evaluate practicality
3. **Resource Planning** - Allocate necessary assets
4. **Task Decomposition** - Break into manageable steps
5. **Progress Tracking** - Monitor advancement
6. **Outcome Validation** - Verify results

## Tool Leverage Patterns

### Tool Selection Criteria
- **Efficiency Gain** - Must improve speed or quality
- **Learning Curve** - Justify investment time
- **Integration** - Must work with existing systems
- **Scalability** - Should support growth

### Automation Rules
- **Repetitive Tasks** - Automate when frequency > threshold
- **Error-Prone Processes** - Automate to reduce mistakes
- **Data Processing** - Automate for consistency
- **Communication** - Automate routine notifications

## Delegation Framework

### Delegation Decision Tree
- **Core Competency** - Keep if strategic advantage
- **Time Sensitivity** - Delegate if urgent and not core
- **Skill Requirement** - Delegate if specialized knowledge needed
- **Cost Efficiency** - Delegate if cheaper than internal

## Resource Prioritization

### Priority Matrix
- **Urgent + Important** - Immediate action
- **Important + Not Urgent** - Schedule and plan
- **Urgent + Not Important** - Delegate or automate
- **Not Urgent + Not Important** - Eliminate or postpone

---

*This OS transforms cognition into applied intelligence through systematic execution.*
"""

    def _format_goal_planning_architecture(self, patterns: Dict[str, Any], traits: Dict[str, str]) -> str:
        return f"""# 🎯 Goal Planning Architecture

*Goal decomposition, planning method, priority logic, and progress tracking*

## Goal Decomposition Structure

{chr(10).join(f"- {goal}" for goal in patterns['goal_decomposition'][:5])}

### Hierarchy Framework
- **Vision** (5-10 years) - Ultimate aspirations
- **Strategic Goals** (1-3 years) - Major milestones
- **Tactical Objectives** (3-12 months) - Specific targets
- **Action Items** (1-4 weeks) - Immediate tasks
- **Daily Habits** (ongoing) - Consistent actions

## Planning Method

### Planning Process
1. **Goal Definition** - Clear, measurable objectives
2. **Gap Analysis** - Current vs desired state
3. **Resource Assessment** - Available assets and constraints
4. **Pathway Design** - Step-by-step approach
5. **Timeline Creation** - Realistic scheduling
6. **Contingency Planning** - Risk mitigation

## Priority Logic

### Decision Framework: {traits.get('decision_style', 'Unknown')}

### Priority Factors
- **Impact** - Potential effect on objectives
- **Urgency** - Time sensitivity
- **Resources** - Required investment
- **Dependencies** - Prerequisites and blockers
- **Strategic Alignment** - Vision consistency

## Progress Tracking Patterns

### Monitoring System
- **Key Metrics** - Quantitative progress indicators
- **Milestone Checkpoints** - Periodic reviews
- **Adaptation Triggers** - When to adjust plans
- **Success Criteria** - Clear completion definitions

### Feedback Loops
- **Weekly Reviews** - Short-term progress
- **Monthly Assessments** - Tactical adjustments
- **Quarterly Planning** - Strategic updates
- **Annual Visioning** - Long-term alignment

---

*This architecture provides operational clarity through structured goal management.*
"""

    def _format_knowledge_framework(self, patterns: Dict[str, Any], signals: Dict[str, int]) -> str:
        return f"""# 📚 Knowledge Framework

*Structured domain depth, core models, key entities, and cross-domain linkages*

## Domain Expertise Structure

{chr(10).join(f"- {model}" for model in patterns['core_models'][:5])}

### Knowledge Depth Analysis
- **Surface Level** - Basic concepts and terminology
- **Operational Understanding** - Practical application
- **Deep Expertise** - Advanced concepts and nuances
- **Mastery** - Innovation and teaching capability

## Core Conceptual Models

### Mental Models Inventory
- **Systems Thinking** - Interconnected component analysis
- **First Principles** - Fundamental truth decomposition
- **Probabilistic Reasoning** - Uncertainty quantification
- **Causal Inference** - Cause-effect relationships
- **Network Effects** - Interconnected value creation

## Key Entities & Systems

### Domain Mapping
- **Technical Systems** - Software, hardware, infrastructure
- **Business Systems** - Organizations, markets, processes
- **Social Systems** - Teams, communities, networks
- **Natural Systems** - Biology, physics, environment

### Entity Relationships
- **Hierarchical** - Parent-child structures
- **Network** - Peer-to-peer connections
- **Causal** - Cause-effect chains
- **Temporal** - Time-based dependencies

## Cross-Domain Linkages

### Interdisciplinary Connections
- **Technology + Business** - Commercial applications
- **Systems + Psychology** - Human behavior patterns
- **Data + Ethics** - Responsible innovation
- **Design + Engineering** - User-centered solutions

### Knowledge Integration Strategy
- **Pattern Recognition** - Identify universal principles
- **Analogical Reasoning** - Apply insights across domains
- **Synthesis** - Create new understanding from combination
- **Abstraction** - Extract generalizable concepts

---

*This framework builds intellectual density through structured knowledge organization.*
"""

    def _format_systems_models(self, patterns: Dict[str, Any], traits: Dict[str, str]) -> str:
        return f"""# 🌐 Systems & Long-Horizon Models

*Systems thinking, long-term simulation, second-order reasoning, and multi-variable modeling*

## Systems Thinking Patterns

{chr(10).join(f"- {system}" for system in patterns['systems_thinking'][:5])}

### Core Systems Principles
- **Interconnectedness** - All elements influence each other
- **Feedback Loops** - Reinforcing and balancing cycles
- **Emergence** - Complex behavior from simple rules
- **Non-linearity** - Disproportionate cause-effect relationships
- **Adaptation** - Systems evolve over time

### Analysis Framework
1. **Boundary Definition** - System scope and interfaces
2. **Component Mapping** - Key elements and relationships
3. **Flow Analysis** - Resource and information movement
4. **Leverage Points** - High-impact intervention areas
5. **Behavior Prediction** - System response to changes

## Long-Term Simulation

### Time Horizon Analysis
- **Immediate (0-6 months)** - Direct consequences
- **Short-term (6-24 months)** - First-order effects
- **Medium-term (2-5 years)** - System adaptations
- **Long-term (5+ years)** - Structural transformations

### Scenario Planning
- **Best Case** - Optimal conditions and outcomes
- **Most Likely** - Probable trajectory
- **Worst Case** - Risk assessment and mitigation
- **Black Swan** - Low-probability, high-impact events

## Second-Order Reasoning

### Consequence Chain Analysis
- **First Order** - Direct effects of actions
- **Second Order** - Consequences of consequences
- **Third Order** - Systemic implications
- **Nth Order** - Cascading effects

### Reasoning Framework: {traits.get('abstraction_level', 'Unknown')}

## Multi-Variable Modeling

### Complexity Management
- **Variable Identification** - Key influencing factors
- **Weight Assignment** - Relative importance
- **Interaction Mapping** - Variable relationships
- **Sensitivity Analysis** - Impact of changes

### Decision Modeling
- **Quantitative Factors** - Measurable variables
- **Qualitative Factors** - Subjective considerations
- **Temporal Factors** - Time-based influences
- **Contextual Factors** - Environmental conditions

---

*These models provide strategic depth through comprehensive systems analysis.*
"""

    def _format_self_stability_profile(self, patterns: Dict[str, Any], signals: Dict[str, int]) -> str:
        return f"""# ⚖️ Self-Stability Profile

*Strength zones, break points, recurring mistakes, and identity constraints*

## Strength Zones

{chr(10).join(f"- {strength}" for strength in patterns['strength_zones'][:5])}

### Core Competencies
- **Analytical Thinking** - Complex problem decomposition
- **Pattern Recognition** - Identifying recurring structures
- **System Building** - Creating robust frameworks
- **Learning Integration** - Rapid skill acquisition

### Performance Sweet Spots
- **Complex Systems** - Multi-variable optimization
- **Strategic Planning** - Long-term vision development
- **Knowledge Synthesis** - Cross-domain integration
- **Process Improvement** - Efficiency enhancement

## Break Points & Limitations

### Known Constraints
{chr(10).join(f"- {limit}" for limit in patterns['strength_zones'][:3] if 'limitation' in limit.lower() or 'weakness' in limit.lower())}

### Stress Triggers
- **Information Overload** - Too many simultaneous inputs
- **Time Pressure** - Urgent decision requirements
- **Ambiguity** - Unclear objectives or constraints
- **Resource Constraints** - Limited assets or support

## Recurring Mistakes

### Pattern Recognition
{chr(10).join(f"- {mistake}" for mistake in patterns['recurring_mistakes'][:5])}

### Error Categories
- **Overcommitment** - Taking on too many responsibilities
- **Analysis Paralysis** - Excessive deliberation
- **Perfectionism** - Unrealistic quality standards
- **Communication Gaps** - Incomplete information sharing

## Identity Constraints

### Core Identity Elements
- **Problem-Solver** - Natural tendency to fix issues
- **System Builder** - Preference for structured approaches
- **Continuous Learner** - Drive for knowledge acquisition
- **Quality Advocate** - Commitment to excellence

### Boundary Conditions
- **Ethical Framework** - Non-negotiable principles
- **Value Alignment** - Consistency with core beliefs
- **Energy Management** - Sustainable pacing requirements
- **Relationship Priorities** - Personal connection maintenance

## Stability Mechanisms

### Self-Regulation Strategies
- **Reflection Practices** - Regular self-assessment
- **Feedback Integration** - External perspective incorporation
- **Stress Management** - Pressure mitigation techniques
- **Recovery Protocols** - Burnout prevention methods

---

*This profile prevents instability in rented cognition through self-awareness and boundary management.*
"""

    def _format_communication_layer(self, patterns: Dict[str, Any], traits: Dict[str, str]) -> str:
        return f"""# 💬 Communication Layer

*Output style, compression level, audience switching, and formatting preferences*

## Output Style Profile

{chr(10).join(f"- {style}" for style in patterns['output_style'][:5])}

### Communication Characteristics
- **Clarity Focus** - Prioritize understanding
- **Conciseness** - Efficient information delivery
- **Structure** - Logical organization
- **Actionability** - Practical guidance

### Style Adaptation: {traits.get('learning_style', 'Unknown')}

## Compression Level

### Information Density Settings
- **High Compression** - Maximum information per word
- **Medium Compression** - Balance of detail and brevity
- **Low Compression** - Comprehensive explanations

### Compression Rules
- **Core Concepts** - Never compress fundamental ideas
- **Supporting Details** - Can be condensed
- **Examples** - Use sparingly for clarity
- **Redundancy** - Eliminate repetitive content

## Audience Switching Rules

### Audience Types
- **Technical** - Domain-specific terminology
- **Business** - ROI and strategic impact
- **General** - Accessible language
- **Executive** - High-level summary

### Adaptation Framework
1. **Audience Assessment** - Knowledge level and needs
2. **Language Selection** - Appropriate terminology
3. **Depth Adjustment** - Technical detail level
4. **Format Optimization** - Presentation style
5. **Outcome Alignment** - Expected takeaways

## Formatting Preferences

### Structural Elements
- **Headings** - Clear hierarchy and navigation
- **Lists** - Scannable bullet points
- **Emphasis** - Strategic highlighting
- **White Space** - Visual separation

### Content Organization
- **Problem-Solution** - Issue-focused structure
- **Chronological** - Time-based progression
- **Thematic** - Topic-based grouping
- **Priority** - Importance ordering

## Presentation Patterns

### Communication Channels
- **Written** - Detailed documentation
- **Verbal** - Interactive discussion
- **Visual** - Diagrams and charts
- **Hybrid** - Multi-modal approach

### Usability Considerations
- **Scannability** - Quick comprehension
- **Searchability** - Easy information retrieval
- **Referenceability** - Clear citation structure
- **Actionability** - Implementation guidance

---

*This layer ensures cognitive outputs are usable, accessible, and effective for diverse audiences.*
"""