from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB_FILE = "mindprint.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_memory_table():
    """Initialize memory data table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            content TEXT NOT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_hash TEXT,
            UNIQUE(file_path, file_hash)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/memory', methods=['POST'])
def store_memory():
    """Store memory data from MEMORY.md files"""
    try:
        data = request.get_json()
        
        if not data or 'memory_data' not in data:
            return jsonify({'error': 'memory_data field is required'}), 400
        
        init_memory_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stored_count = 0
        updated_count = 0
        
        for memory_item in data['memory_data']:
            file_path = memory_item.get('file_path')
            content = memory_item.get('content')
            file_hash = memory_item.get('file_hash')
            
            if not file_path or not content:
                continue
            
            # Check if record exists with same file_path and hash
            cursor.execute(
                'SELECT id FROM memory_data WHERE file_path = ? AND file_hash = ?',
                (file_path, file_hash)
            )
            existing = cursor.fetchone()
            
            if existing:
                updated_count += 1
                cursor.execute('''
                    UPDATE memory_data 
                    SET content = ?, scanned_at = CURRENT_TIMESTAMP 
                    WHERE file_path = ? AND file_hash = ?
                ''', (content, file_path, file_hash))
            else:
                stored_count += 1
                cursor.execute('''
                    INSERT INTO memory_data (file_path, content, file_hash)
                    VALUES (?, ?, ?)
                ''', (file_path, content, file_hash))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'stored': stored_count,
            'updated': updated_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory', methods=['GET'])
def get_memory():
    """Retrieve all stored memory data"""
    try:
        init_memory_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM memory_data ORDER BY scanned_at DESC')
        memories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(memories),
            'memories': memories
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/<int:memory_id>', methods=['GET'])
def get_memory_by_id(memory_id):
    """Retrieve specific memory data by ID"""
    try:
        init_memory_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM memory_data WHERE id = ?', (memory_id,))
        memory = cursor.fetchone()
        conn.close()
        
        if memory:
            return jsonify({
                'success': True,
                'memory': dict(memory)
            })
        else:
            return jsonify({'error': 'Memory not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'mindprint-memory-api'
    })

if __name__ == '__main__':
    init_memory_table()
    app.run(debug=True, host='0.0.0.0', port=5000)
