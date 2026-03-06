import os
from typing import List, Dict, Optional
from mem0 import Memory
from ..core.config import settings

class MemoryService:
    def __init__(self):
        # Configure Mem0 for Local Usage
        # We use 'local' provider for embeddings and 'qdrant' for vector store (default local)
        # However, for the best multi-turn experience, we use the Groq model if available
        # or stick to the custom local config.
        
        # Ensure local directory exists
        db_path = os.path.join(os.getcwd(), "data", "mem0_db")
        os.makedirs(db_path, exist_ok=True)
        
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "path": db_path,
                }
            },
            "llm": {
                "provider": "groq",
                "config": {
                    "model": "llama-3.1-8b-instant",
                    "api_key": settings.GROQ_API_KEY,
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                }
            }
        }
        
        try:
            self.memory = Memory.from_config(config)
        except Exception as e:
            print(f"Mem0 Init Error: {e}. Falling back to default.")
            # If config fails, try a minimal local setup
            self.memory = Memory() 

    def add_interaction(self, user_id: str, query: str, answer: str):
        """Extract facts from a conversation turn and store them."""
        try:
            messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": answer}
            ]
            self.memory.add(messages, user_id=user_id)
        except Exception as e:
            print(f"Memory Add Error: {e}")

    def get_relevant_memories(self, user_id: str, query: str) -> str:
        """Search for relevant past interactions/facts."""
        try:
            memories = self.memory.search(query, user_id=user_id)
            if not memories:
                return ""
            
            # Format memories into a readable string for the prompt
            context = "\n".join([f"- {m['memory']}" for m in memories])
            return context
        except Exception as e:
            print(f"Memory Search Error: {e}")
            return ""

    def forget_user(self, user_id: str):
        """Clear all memories for a user."""
        try:
            self.memory.delete_all(user_id=user_id)
        except Exception as e:
            print(f"Memory Delete Error: {e}")
