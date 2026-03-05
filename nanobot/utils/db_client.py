"""Database client for syncing cognition data to remote database."""

import json
import os
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .hardware_id import get_hardware_id


class CognitionDBClient:
    """Client for syncing cognition data to the database API."""
    
    def __init__(self, api_url: str = None, timeout: int = 30):
        # Auto-detect API URL if not provided
        if not api_url:
            # Prioritize environment variable
            env_url = os.getenv("MINDPRINT_API_URL")
            if env_url:
                self.api_url = env_url.rstrip('/')
            else:
                try:
                    # Try to get URL from health check
                    response = requests.get("http://localhost:5000/api/health", timeout=5)
                    if response.status_code == 200:
                        self.api_url = "http://localhost:5000"
                    else:
                        self.api_url = "http://localhost:5000"
                except:
                    self.api_url = "http://localhost:5000"
        else:
            self.api_url = api_url.rstrip('/')
        
        self.timeout = timeout
        self.hardware_id = get_hardware_id()
    
    def sync_cognition_file(self, file_path: Path, content: str) -> bool:
        """Sync cognition file to database."""
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Prepare payload
            payload = {
                "memory_data": [{
                    "file_path": str(file_path),
                    "content": content,
                    "file_hash": file_hash,
                    "user_id": self.hardware_id,
                    "metadata": {
                        "type": "cognition_profile",
                        "version": "2.0",
                        "generated": datetime.now().isoformat(),
                        "hardware_id": self.hardware_id,
                        "file_type": "cognition.md"
                    }
                }]
            }
            
            # Send to database
            response = requests.post(
                f"{self.api_url}/api/memory",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Cognition synced to database (stored: {result.get('stored', 0)}, updated: {result.get('updated', 0)})")
                return True
            else:
                print(f"Failed to sync cognition: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Database sync error: {e}")
            return False
        except Exception as e:
            print(f"Sync error: {e}")
            return False
    
    def sync_cognition_json(self, file_path: Path, content: str) -> bool:
        """Sync cognition JSON file to database."""
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Parse JSON to extract metadata
            try:
                cognition_data = json.loads(content)
                model_version = cognition_data.get("model_version", "2.0")
                dominant_traits = cognition_data.get("dominant_traits", {})
                signals = cognition_data.get("behavioral_signals", {})
            except json.JSONDecodeError:
                model_version = "2.0"
                dominant_traits = {}
                signals = {}
            
            # Prepare payload
            payload = {
                "memory_data": [{
                    "file_path": str(file_path),
                    "content": content,
                    "file_hash": file_hash,
                    "user_id": self.hardware_id,
                    "metadata": {
                        "type": "cognition_profile_json",
                        "version": model_version,
                        "generated": datetime.now().isoformat(),
                        "hardware_id": self.hardware_id,
                        "file_type": "cognition.json",
                        "dominant_traits": dominant_traits,
                        "behavioral_signals": signals
                    }
                }]
            }
            
            # Send to database
            response = requests.post(
                f"{self.api_url}/api/memory",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Cognition JSON synced to database (stored: {result.get('stored', 0)}, updated: {result.get('updated', 0)})")
                return True
            else:
                print(f"Failed to sync cognition JSON: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Database sync error: {e}")
            return False
        except Exception as e:
            print(f"Sync error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to database API."""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"Database connection healthy (status: {health.get('status')})")
                return True
            else:
                print(f"Database unhealthy: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to database: Connection refused at {self.api_url}")
            print(f"Tip: Start the MindPrint backend using 'nanobot mindprint server start' or 'make db-api'")
            return False
        except Exception as e:
            print(f"Cannot connect to database: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status and statistics."""
        try:
            response = requests.get(
                f"{self.api_url}/api/memory/stats",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                stats = response.json().get("stats", {})
                return {
                    "connected": True,
                    "total_memories": stats.get("total_memories", 0),
                    "unique_files": stats.get("unique_files", 0),
                    "last_scan": stats.get("last_scan"),
                    "hardware_id": self.hardware_id
                }
            else:
                return {"connected": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"connected": False, "error": str(e)}


if __name__ == "__main__":
    # Test the client
    client = CognitionDBClient()
    print("Hardware ID:", client.hardware_id)
    print("Connection test:", client.test_connection())
    print("Sync status:", client.get_sync_status())
