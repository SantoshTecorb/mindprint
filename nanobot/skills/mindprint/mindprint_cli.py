import os
import sys
import uuid
import hashlib
import json
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import platform
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mindprint")

# Try to import nanobot config bits if available, otherwise use defaults
try:
    from nanobot.config.loader import load_config
    config = load_config()
    db_url = config.tools.mindprint.database_url
    user_id = config.tools.mindprint.user_id
except ImportError:
    db_url = os.getenv("DATABASE_URL", "postgresql://nanobot:password@localhost/memorydb")
    user_id = ""

def get_hardware_id():
    """Generate a stable hardware-based ID."""
    node = uuid.getnode()
    return hashlib.md5(str(node).encode()).hexdigest()[:12]

def get_db_connection(url):
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def register_seller(db_url, uid, workspace_root):
    """Collect system telemetry and register seller metadata in the database."""
    try:
        data = {
            "user_id": uid,
            "hostname": socket.gethostname(),
            "os_name": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "install_path": str(Path(workspace_root).expanduser().resolve()),
            "metadata": {
                "processor": platform.processor(),
                "machine": platform.machine(),
                "node": platform.node(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        conn = get_db_connection(db_url)
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sellers (user_id, hostname, os_name, os_version, python_version, install_path, last_seen, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                hostname = EXCLUDED.hostname,
                os_name = EXCLUDED.os_name,
                os_version = EXCLUDED.os_version,
                python_version = EXCLUDED.python_version,
                install_path = EXCLUDED.install_path,
                last_seen = EXCLUDED.last_seen,
                metadata = EXCLUDED.metadata
        """, (
            data['user_id'], data['hostname'], data['os_name'], data['os_version'],
            data['python_version'], data['install_path'], datetime.utcnow(),
            json.dumps(data['metadata'])
        ))
        
        cursor.close()
        conn.close()
        logger.info(f"Seller telemetry registered for: {uid}")
        
    except Exception as e:
        logger.error(f"Failed to register seller telemetry: {e}")

def register_buyer(db_url, uid, workspace_root):
    """Collect system telemetry and register buyer metadata in the database."""
    try:
        data = {
            "user_id": uid,
            "hostname": socket.gethostname(),
            "os_name": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "install_path": str(Path(workspace_root).expanduser().resolve()),
            "metadata": {
                "processor": platform.processor(),
                "machine": platform.machine(),
                "node": platform.node(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        conn = get_db_connection(db_url)
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO buyers (user_id, hostname, os_name, os_version, python_version, install_path, last_seen, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                hostname = EXCLUDED.hostname,
                os_name = EXCLUDED.os_name,
                os_version = EXCLUDED.os_version,
                python_version = EXCLUDED.python_version,
                install_path = EXCLUDED.install_path,
                last_seen = EXCLUDED.last_seen,
                metadata = EXCLUDED.metadata
        """, (
            data['user_id'], data['hostname'], data['os_name'], data['os_version'],
            data['python_version'], data['install_path'], datetime.utcnow(),
            json.dumps(data['metadata'])
        ))
        
        cursor.close()
        conn.close()
        logger.info(f"Buyer telemetry registered for: {uid}")
        
    except Exception as e:
        logger.error(f"Failed to register buyer telemetry: {e}")

def sync_cognition(workspace_root, db_url, uid):
    """Scan for .mindprint/ directories and sync all .md files within."""
    conn = get_db_connection(db_url)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Ensure ID
    if not uid:
        uid = get_hardware_id()
    
    workspace_path = Path(workspace_root).expanduser().resolve()
    
    # Register telemetry first
    register_seller(db_url, uid, workspace_root)
    
    logger.info(f"Scanning {workspace_path} for .mindprint/ folders...")
    
    synced_count = 0
    # Search for directories named '.mindprint'
    for mindprint_dir in workspace_path.rglob(".mindprint"):
        if not mindprint_dir.is_dir():
            continue
            
        logger.info(f"Found folder: {mindprint_dir}")
        # Sync every .md file inside the .mindprint folder
        for md_file in mindprint_dir.glob("*.md"):
            try:
                logger.info(f"Processing {md_file}...")
                content = md_file.read_text(encoding="utf-8")
                file_hash = hashlib.md5(content.encode()).hexdigest()
                rel_path = str(md_file.relative_to(workspace_path))
                
                # Upsert into memory_data
                cursor.execute("""
                    INSERT INTO memory_data (file_path, content, file_hash, user_id, scanned_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (file_path, file_hash) 
                    DO UPDATE SET content = EXCLUDED.content, scanned_at = EXCLUDED.scanned_at
                """, (rel_path, content, file_hash, uid, datetime.utcnow()))
                
                synced_count += 1
                logger.info(f"Successfully synced {rel_path}")
            except Exception as e:
                logger.error(f"Failed to sync {md_file}: {e}")
            
    cursor.close()
    conn.close()
    logger.info(f"Sync complete. {synced_count} files processed.")

def pull_persona_by_token(token, db_url, workspace_root):
    """Download all cognitive assets for a persona via rental token."""
    conn = get_db_connection(db_url)
    if not conn:
        return
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Register buyer telemetry first
        # We use a secondary UID lookup for buyers if config isn't available
        buyer_uid = user_id if 'user_id' in globals() and user_id else get_hardware_id()
        register_buyer(db_url, buyer_uid, workspace_root)

        # 1. Map Token to Seller Hardware ID (user_id)
        logger.info(f"Verifying token: {token}")
        cursor.execute("SELECT seller_user_id FROM rentals WHERE token = %s", (token,))
        rental = cursor.fetchone()
        
        if not rental:
            logger.error(f"Invalid or expired token: {token}")
            return
            
        seller_uid = rental['seller_user_id']
        logger.info(f"Token valid. Pulling assets for seller: {seller_uid}")

        # 2. Retrieve all files for this seller
        cursor.execute("SELECT file_path, content FROM memory_data WHERE user_id = %s", (seller_uid,))
        assets = cursor.fetchall()
        
        if not assets:
            logger.warning(f"No cognitive assets found for seller: {seller_uid}")
            return

        # 3. Save to structured subfolders
        persona_base_dir = Path(workspace_root).expanduser() / "personas" / seller_uid
        persona_base_dir.mkdir(parents=True, exist_ok=True)
        
        for asset in assets:
            target_file = persona_base_dir / asset['file_path']
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(asset['content'], encoding="utf-8")
            logger.info(f"Saved: {target_file}")
        
        logger.info(f"Successfully pulled {len(assets)} assets for persona {seller_uid}")
        
    except Exception as e:
        logger.error(f"Failed to pull persona for token {token}: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MindPrint CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--workspace", default=".")
    
    pull_parser = subparsers.add_parser("pull")
    pull_parser.add_argument("id")
    pull_parser.add_argument("--workspace", default=".")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        sync_cognition(args.workspace, db_url, user_id)
    elif args.command == "pull":
        pull_persona_by_token(args.id, db_url, args.workspace)
    else:
        parser.print_help()
