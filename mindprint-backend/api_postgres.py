from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://nanobot:password@localhost/memorydb')

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Database Model
class MemoryData(Base):
    __tablename__ = 'memory_data'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    file_hash = Column(String(32), nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))
    extra_metadata = Column(Text)
    
    __table_args__ = (
        UniqueConstraint('file_path', 'file_hash', name='uix_file_path_hash'),
    )

class Rental(Base):
    __tablename__ = 'rentals'
    
    id = Column(Integer, primary_key=True)
    token = Column(String(100), unique=True, nullable=False)
    seller_user_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class Seller(Base):
    __tablename__ = 'sellers'
    
    user_id = Column(String(100), primary_key=True)
    hostname = Column(Text)
    os_name = Column(Text)
    os_version = Column(Text)
    python_version = Column(Text)
    install_path = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text) # JSON string

class Buyer(Base):
    __tablename__ = 'buyers'
    
    user_id = Column(String(100), primary_key=True)
    hostname = Column(Text)
    os_name = Column(Text)
    os_version = Column(Text)
    python_version = Column(Text)
    install_path = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text) # JSON string

def get_db_connection():
    """Get direct PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    try:
        # Create tables
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        
        # Create indexes for better performance
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_file_path ON memory_data(file_path);
                CREATE INDEX IF NOT EXISTS idx_memory_file_hash ON memory_data(file_hash);
                CREATE INDEX IF NOT EXISTS idx_memory_scanned_at ON memory_data(scanned_at);
                CREATE INDEX IF NOT EXISTS idx_memory_user_id ON memory_data(user_id);
                
                -- Full-text search index on content
                CREATE INDEX IF NOT EXISTS idx_memory_content_fts ON memory_data USING gin(to_tsvector('english', content));
            """)
            
            cursor.close()
            conn.close()
            print("✅ Database indexes created successfully")
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

@app.route('/api/memory', methods=['POST'])
def store_memory():
    """Store memory data from MEMORY.md files"""
    try:
        data = request.get_json()
        
        if not data or 'memory_data' not in data:
            return jsonify({'error': 'memory_data field is required'}), 400
        
        init_database()
        session = Session()
        
        stored_count = 0
        updated_count = 0
        
        for memory_item in data['memory_data']:
            file_path = memory_item.get('file_path')
            content = memory_item.get('content')
            file_hash = memory_item.get('file_hash')
            user_id = memory_item.get('user_id', 'default')
            metadata = json.dumps(memory_item.get('metadata', {}))
            
            if not file_path or not content:
                continue
            
            # Check if record exists with same file_path and hash
            existing = session.query(MemoryData).filter_by(
                file_path=file_path, 
                file_hash=file_hash
            ).first()
            
            if existing:
                # Update existing record
                existing.content = content
                existing.scanned_at = datetime.utcnow()
                existing.extra_metadata = metadata
                updated_count += 1
            else:
                # Create new record
                new_memory = MemoryData(
                    file_path=file_path,
                    content=content,
                    file_hash=file_hash,
                    user_id=user_id,
                    extra_metadata=metadata
                )
                session.add(new_memory)
                stored_count += 1
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'stored': stored_count,
            'updated': updated_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory', methods=['GET'])
def get_memory():
    """Retrieve all stored memory data"""
    try:
        init_database()
        session = Session()
        
        # Parse query parameters
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search')
        
        query = session.query(MemoryData)
        
        # Apply filters
        if user_id:
            query = query.filter(MemoryData.user_id == user_id)
        
        if search:
            # Full-text search
            query = query.filter(
                "to_tsvector('english', content) @@ to_tsquery(%s)"
            ).params(search)
        
        # Apply pagination and ordering
        memories = query.order_by(MemoryData.scanned_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict
        result = []
        for memory in memories:
            result.append({
                'id': memory.id,
                'file_path': memory.file_path,
                'content': memory.content,
                'file_hash': memory.file_hash,
                'scanned_at': memory.scanned_at.isoformat(),
                'user_id': memory.user_id,
                'metadata': json.loads(memory.extra_metadata) if memory.extra_metadata else {}
            })
        
        session.close()
        
        return jsonify({
            'success': True,
            'count': len(result),
            'memories': result,
            'offset': offset,
            'limit': limit
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/<int:memory_id>', methods=['GET'])
def get_memory_by_id(memory_id):
    """Retrieve specific memory data by ID"""
    try:
        init_database()
        session = Session()
        
        memory = session.query(MemoryData).filter(MemoryData.id == memory_id).first()
        
        if memory:
            result = {
                'id': memory.id,
                'file_path': memory.file_path,
                'content': memory.content,
                'file_hash': memory.file_hash,
                'scanned_at': memory.scanned_at.isoformat(),
                'user_id': memory.user_id,
                'metadata': json.loads(memory.extra_metadata) if memory.extra_metadata else {}
            }
            session.close()
            return jsonify({
                'success': True,
                'memory': result
            })
        else:
            session.close()
            return jsonify({'error': 'Memory not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/search', methods=['POST'])
def search_memory():
    """Advanced search in memory content"""
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        user_id = data.get('user_id')
        limit = data.get('limit', 50)
        
        if not query_text:
            return jsonify({'error': 'query parameter is required'}), 400
        
        init_database()
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Full-text search query
        search_query = """
            SELECT id, file_path, content, file_hash, scanned_at, user_id, extra_metadata,
                   ts_rank(to_tsvector('english', content), to_tsquery('english', %s)) as rank
            FROM memory_data 
            WHERE to_tsvector('english', content) @@ to_tsquery('english', %s)
        """
        params = [query_text, query_text]
        
        if user_id:
            search_query += " AND user_id = %s"
            params.append(user_id)
        
        search_query += " ORDER BY rank DESC, scanned_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(search_query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to strings
        for result in results:
            result['scanned_at'] = result['scanned_at'].isoformat()
            if result['extra_metadata']:
                result['metadata'] = json.loads(result['extra_metadata'])
                del result['extra_metadata']
        
        return jsonify({
            'success': True,
            'count': len(results),
            'memories': [dict(result) for result in results],
            'query': query_text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/stats', methods=['GET'])
def get_memory_stats():
    """Get statistics about stored memory data"""
    try:
        init_database()
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get various statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_memories,
                COUNT(DISTINCT file_path) as unique_files,
                COUNT(DISTINCT user_id) as unique_users,
                MAX(scanned_at) as last_scan,
                MIN(scanned_at) as first_scan
            FROM memory_data
        """
        
        cursor.execute(stats_query)
        stats = cursor.fetchone()
        
        # Get file size statistics
        cursor.execute("""
            SELECT 
                AVG(LENGTH(content)) as avg_content_size,
                MAX(LENGTH(content)) as max_content_size,
                MIN(LENGTH(content)) as min_content_size
            FROM memory_data
        """)
        size_stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Convert to regular dict and format datetime
        result = dict(stats)
        result.update(dict(size_stats))
        result['last_scan'] = result['last_scan'].isoformat() if result['last_scan'] else None
        result['first_scan'] = result['first_scan'].isoformat() if result['first_scan'] else None
        
        return jsonify({
            'success': True,
            'stats': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rentals', methods=['POST'])
def create_rental():
    """Create a new rental token (Marketplace side logic)"""
    try:
        data = request.get_json()
        seller_uid = data.get('seller_user_id')
        
        if not seller_uid:
            return jsonify({'error': 'seller_user_id is required'}), 400
            
        token = f"mp@{hashlib.sha256(os.urandom(32)).hexdigest()[:12]}"
        
        session = Session()
        new_rental = Rental(token=token, seller_user_id=seller_uid)
        session.add(new_rental)
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'token': token,
            'seller_user_id': seller_uid
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sellers/telemetry', methods=['POST'])
def update_seller_telemetry():
    """Register or update seller installation metadata"""
    try:
        data = request.get_json()
        uid = data.get('user_id')
        
        if not uid:
            return jsonify({'error': 'user_id is required'}), 400
            
        session = Session()
        seller = session.query(Seller).filter_by(user_id=uid).first()
        
        if not seller:
            seller = Seller(user_id=uid, first_seen=datetime.utcnow())
            session.add(seller)
            
        seller.hostname = data.get('hostname')
        seller.os_name = data.get('os_name')
        seller.os_version = data.get('os_version')
        seller.python_version = data.get('python_version')
        seller.install_path = data.get('install_path')
        seller.last_seen = datetime.utcnow()
        seller.metadata_json = json.dumps(data.get('metadata', {}))
        
        session.commit()
        session.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/buyers/telemetry', methods=['POST'])
def update_buyer_telemetry():
    """Register or update buyer installation metadata"""
    try:
        data = request.get_json()
        uid = data.get('user_id')
        
        if not uid:
            return jsonify({'error': 'user_id is required'}), 400
            
        session = Session()
        buyer = session.query(Buyer).filter_by(user_id=uid).first()
        
        if not buyer:
            buyer = Buyer(user_id=uid, first_seen=datetime.utcnow())
            session.add(buyer)
            
        buyer.hostname = data.get('hostname')
        buyer.os_name = data.get('os_name')
        buyer.os_version = data.get('os_version')
        buyer.python_version = data.get('python_version')
        buyer.install_path = data.get('install_path')
        buyer.last_seen = datetime.utcnow()
        buyer.metadata_json = json.dumps(data.get('metadata', {}))
        
        session.commit()
        session.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with database status"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return jsonify({
            'status': 'healthy' if db_status == 'connected' else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'mindprint-memory-api-postgres',
            'database': db_status,
            'database_url': DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'mindprint-memory-api-postgres',
            'database': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
