import os
import json
import requests
import litellm
import re
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import SkillCache, BuyerSkillUsage, Rental
from ..core.config import settings

# Set Groq API Key for LiteLLM if provided
if settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

class SkillDiscoveryService:
    def __init__(self, db: Session):
        self.db = db
        self.github_raw_base = "https://raw.githubusercontent.com/openclaw/skills/main/skills"
        self.awesome_registry_url = "https://raw.githubusercontent.com/VoltAgent/awesome-openclaw-skills/main/README.md"
        self.index_path = os.path.join(os.path.dirname(__file__), "skill_index.json")

    def refresh_global_index(self) -> List[Dict]:
        """Fetch and parse the full 1,700+ skill registry from Awesome OpenClaw Skills."""
        # 1. Check if local index is fresh ( < 24 hours )
        if os.path.exists(self.index_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(self.index_path))
            if datetime.now() - mtime < timedelta(hours=24):
                with open(self.index_path, "r") as f:
                    return json.load(f)

        # 2. Fetch README from Awesome Registry
        try:
            response = requests.get(self.awesome_registry_url, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch registry: {response.status_code}")
                return []
            
            content = response.text
            
            # 3. Parse Skills using Regex
            # Assuming format: [Skill Name](https://github.com/openclaw/skills/tree/main/skills/author/slug/SKILL.md) - Description
            skills = []
            
            # Refined regex for the OpenClaw skills repo pattern
            pattern = r'\[(.*?)\]\(.*?skills/(.*?/.*?)/SKILL.md\)\s*-\s*(.*)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                name = match.group(1)
                slug = match.group(2).strip('/')
                description = match.group(3).strip()
                
                skills.append({
                    "name": name,
                    "slug": slug,
                    "description": description
                })
            
            if skills:
                with open(self.index_path, "w") as f:
                    json.dump(skills, f, indent=2)
                print(f"Refreshed global index: {len(skills)} skills found.")
                
            return skills
        except Exception as e:
            print(f"Error refreshing index: {e}")
            return []

    async def detect_intent(self, user_query: str) -> Optional[str]:
        """Detect if the user intent matches a skill in the global registry."""
        skills = self.refresh_global_index()
        if not skills:
            return None
            
        # 1. Semantic Match using LLM (Optimized for speed)
        # We send a chunk of relevant skills or let the LLM search
        # Since 1700 skills is too much for one prompt, we do a 2-stage approach:
        # A. Keyword filter (coarse)
        # B. LLM rank (fine)
        
        query_words = set(re.findall(r'\w+', user_query.lower()))
        candidates = []
        for s in skills:
            # Simple keyword overlap between query and (name + description)
            text = (s["name"] + " " + s["description"]).lower()
            if any(word in text for word in query_words if len(word) > 3):
                candidates.append(s)
        
        # Limit to top 20 candidates for LLM ranking
        candidates = candidates[:20]
        
        if not candidates:
            # Fallback: if no keyword match, try a more general LLM "search"
            # (In a real production app, we would use Vector Search here)
            return None

        try:
            candidates_str = "\n".join([f"{s['slug']}: {s['description']}" for s in candidates])
            prompt = f"""Identify the most relevant Skill Slug for the query. 
If none fit perfectly, reply 'none'.

QUERY: "{user_query}"

CANDIDATES:
{candidates_str}

REPLY WITH SLUG ONLY:"""
            
            response = litellm.completion(
                model=settings.CONSULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            detected = response.choices[0].message.content.strip().lower()
            
            # Verify the detected slug actually exists in our candidates
            if any(s["slug"] == detected for s in candidates):
                return detected
        except:
            pass
            
        return None

    def get_skill_instructions(self, slug: str) -> Optional[str]:
        """Get skill instructions from cache or GitHub Raw."""
        # 1. Check Cache
        cached = self.db.query(SkillCache).filter_by(slug=slug).first()
        if cached:
            return cached.content
            
        # 2. Fetch from GitHub Raw
        try:
            url = f"{self.github_raw_base}/{slug}/SKILL.md"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                # Update Cache
                new_cache = SkillCache(slug=slug, content=content)
                self.db.add(new_cache)
                self.db.commit()
                return content
        except Exception as e:
            print(f"Error fetching skill {slug}: {e}")
            
        return None

    def track_usage(self, rental_id: int, slug: str):
        """Track which skill a user is using."""
        usage = BuyerSkillUsage(rental_id=rental_id, skill_slug=slug)
        self.db.add(usage)
        self.db.commit()

    def get_user_skills(self, rental_id: int) -> List[str]:
        """Get list of skills used by this rental session."""
        usages = self.db.query(BuyerSkillUsage).filter_by(rental_id=rental_id).all()
        return list(set([u.skill_slug for u in usages]))
