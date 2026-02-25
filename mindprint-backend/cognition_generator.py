#!/usr/bin/env python3
"""
Cognition Generator
Reads memory data from database and processes it to generate cognition.md file
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os
from collections import defaultdict
import re

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://nanobot:your_secure_password_here@localhost/memorydb')

def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def fetch_all_memory_data():
    """Fetch all memory data from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, file_path, content, file_hash, scanned_at, user_id, extra_metadata
            FROM memory_data 
            ORDER BY scanned_at DESC
        """)
        
        memories = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(memory) for memory in memories]
        
    except Exception as e:
        print(f"Error fetching memory data: {e}")
        return []

def extract_sections(content):
    """Extract sections from memory content"""
    sections = {}
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    for line in lines:
        if line.startswith('## '):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def process_memory_data(memories):
    """Process memory data to extract insights"""
    processed_data = {
        'user_information': defaultdict(list),
        'preferences': defaultdict(list),
        'project_context': defaultdict(list),
        'important_notes': defaultdict(list),
        'file_summary': [],
        'temporal_analysis': {},
        'patterns': {}
    }
    
    # Process each memory file
    for memory in memories:
        sections = extract_sections(memory['content'])
        file_info = {
            'file_path': memory['file_path'],
            'scanned_at': memory['scanned_at'].isoformat() if hasattr(memory['scanned_at'], 'isoformat') else str(memory['scanned_at']),
            'user_id': memory['user_id']
        }
        
        # Extract user information
        if 'User Information' in sections:
            user_info = sections['User Information']
            if user_info and user_info != '(Important facts about the user)':
                processed_data['user_information'][memory['user_id']].append({
                    'content': user_info,
                    'source': file_info
                })
        
        # Extract preferences
        if 'Preferences' in sections:
            preferences = sections['Preferences']
            if preferences and preferences != '(User preferences learned over time)':
                processed_data['preferences'][memory['user_id']].append({
                    'content': preferences,
                    'source': file_info
                })
        
        # Extract project context
        if 'Project Context' in sections:
            project_context = sections['Project Context']
            if project_context and project_context != '(Information about ongoing projects)':
                processed_data['project_context'][memory['user_id']].append({
                    'content': project_context,
                    'source': file_info
                })
        
        # Extract important notes
        if 'Important Notes' in sections:
            notes = sections['Important Notes']
            if notes and notes != '(Things to remember)':
                processed_data['important_notes'][memory['user_id']].append({
                    'content': notes,
                    'source': file_info
                })
        
        processed_data['file_summary'].append(file_info)
    
    # Analyze patterns
    processed_data['patterns'] = analyze_patterns(memories)
    processed_data['temporal_analysis'] = analyze_temporal_patterns(memories)
    
    return processed_data

def analyze_patterns(memories):
    """Analyze patterns in memory data"""
    patterns = {
        'total_memories': len(memories),
        'unique_users': len(set(m['user_id'] for m in memories)),
        'file_types': defaultdict(int),
        'content_length_stats': {},
        'most_active_users': []
    }
    
    # File type analysis
    for memory in memories:
        ext = os.path.splitext(memory['file_path'])[1]
        patterns['file_types'][ext] += 1
    
    # Content length statistics
    lengths = [len(memory['content']) for memory in memories]
    if lengths:
        patterns['content_length_stats'] = {
            'min': min(lengths),
            'max': max(lengths),
            'avg': sum(lengths) / len(lengths)
        }
    
    # Most active users
    user_counts = defaultdict(int)
    for memory in memories:
        user_counts[memory['user_id']] += 1
    
    patterns['most_active_users'] = sorted(
        user_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    return patterns

def analyze_temporal_patterns(memories):
    """Analyze temporal patterns in memory data"""
    temporal = {
        'date_distribution': defaultdict(int),
        'recent_activity': [],
        'oldest_memory': None,
        'newest_memory': None
    }
    
    if not memories:
        return temporal
    
    # Sort by date
    sorted_memories = sorted(memories, key=lambda x: x['scanned_at'])
    
    temporal['oldest_memory'] = sorted_memories[0]['scanned_at'].isoformat()
    temporal['newest_memory'] = sorted_memories[-1]['scanned_at'].isoformat()
    
    # Date distribution
    for memory in memories:
        date = memory['scanned_at'].date().isoformat()  # Extract date part
        temporal['date_distribution'][date] += 1
    
    # Recent activity (last 10)
    temporal['recent_activity'] = [
        {
            'file_path': m['file_path'],
            'scanned_at': m['scanned_at'].isoformat(),
            'user_id': m['user_id']
        }
        for m in sorted_memories[-10:]
    ]
    
    return temporal

def generate_cognition_md(processed_data, output_file='cognition.md'):
    """Generate cognition.md file from processed data"""
    
    content = []
    content.append("# Cognition Analysis")
    content.append("")
    content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    content.append("")
    
    # Executive Summary
    content.append("## Executive Summary")
    content.append("")
    patterns = processed_data['patterns']
    content.append(f"- **Total Memories**: {patterns['total_memories']}")
    content.append(f"- **Unique Users**: {patterns['unique_users']}")
    content.append(f"- **File Types**: {', '.join(patterns['file_types'].keys())}")
    content.append(f"- **Average Content Length**: {patterns['content_length_stats'].get('avg', 0):.0f} characters")
    content.append("")
    
    # User Profiles
    content.append("## User Profiles")
    content.append("")
    
    for user_id in processed_data['user_information']:
        content.append(f"### User: {user_id}")
        content.append("")
        
        # User Information
        user_info = processed_data['user_information'][user_id]
        if user_info:
            content.append("#### User Information")
            for info in user_info:
                content.append(f"- {info['content']}")
            content.append("")
        
        # Preferences
        preferences = processed_data['preferences'][user_id]
        if preferences:
            content.append("#### Preferences")
            for pref in preferences:
                content.append(f"- {pref['content']}")
            content.append("")
        
        # Project Context
        projects = processed_data['project_context'][user_id]
        if projects:
            content.append("#### Project Context")
            for project in projects:
                content.append(f"- {project['content']}")
            content.append("")
        
        # Important Notes
        notes = processed_data['important_notes'][user_id]
        if notes:
            content.append("#### Important Notes")
            for note in notes:
                content.append(f"- {note['content']}")
            content.append("")
    
    # Patterns Analysis
    content.append("## Patterns Analysis")
    content.append("")
    
    patterns = processed_data['patterns']
    content.append("### Activity Patterns")
    content.append("")
    for user_id, count in patterns['most_active_users']:
        content.append(f"- **{user_id}**: {count} memories")
    content.append("")
    
    content.append("### File Distribution")
    content.append("")
    for ext, count in patterns['file_types'].items():
        content.append(f"- **{ext}**: {count} files")
    content.append("")
    
    # Temporal Analysis
    content.append("## Temporal Analysis")
    content.append("")
    
    temporal = processed_data['temporal_analysis']
    content.append(f"**Time Range**: {temporal['oldest_memory']} to {temporal['newest_memory']}")
    content.append("")
    
    content.append("### Recent Activity")
    content.append("")
    for activity in temporal['recent_activity'][-5:]:  # Last 5 activities
        content.append(f"- **{activity['scanned_at']}**: {activity['file_path']} ({activity['user_id']})")
    content.append("")
    
    # Insights and Recommendations
    content.append("## Insights and Recommendations")
    content.append("")
    
    # Generate insights based on data
    insights = generate_insights(processed_data)
    for insight in insights:
        content.append(f"- {insight}")
    content.append("")
    
    # File Inventory
    content.append("## File Inventory")
    content.append("")
    content.append("| File Path | User | Last Scanned |")
    content.append("|-----------|------|--------------|")
    
    for file_info in processed_data['file_summary'][-20:]:  # Last 20 files
        file_path = file_info['file_path']
        user_id = file_info['user_id']
        scanned_at = file_info['scanned_at'].split('T')[0] if isinstance(file_info['scanned_at'], str) else file_info['scanned_at'].date().isoformat()
        content.append(f"| {file_path} | {user_id} | {scanned_at} |")
    
    content.append("")
    content.append("---")
    content.append("")
    content.append("*This cognition analysis was automatically generated from memory data.*")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Cognition analysis generated: {output_file}")

def generate_insights(processed_data):
    """Generate insights from processed data"""
    insights = []
    
    patterns = processed_data['patterns']
    
    # User activity insights
    if patterns['unique_users'] > 1:
        insights.append(f"Multi-user environment detected with {patterns['unique_users']} active users")
    elif patterns['unique_users'] == 1:
        insights.append("Single-user environment with consistent memory tracking")
    
    # Content volume insights
    if patterns['total_memories'] > 50:
        insights.append("High memory activity - consider implementing content categorization")
    elif patterns['total_memories'] < 10:
        insights.append("Low memory volume - encourage more frequent memory updates")
    
    # File type insights
    if '.md' in patterns['file_types'] and patterns['file_types']['.md'] > 0:
        insights.append(f"Markdown files dominate ({patterns['file_types']['.md']} files) - good documentation practices")
    
    # Temporal insights
    temporal = processed_data['temporal_analysis']
    if temporal['oldest_memory'] and temporal['newest_memory']:
        oldest_date = temporal['oldest_memory'].split(' ')[0]
        newest_date = temporal['newest_memory'].split(' ')[0]
        insights.append(f"Memory tracking spans from {oldest_date} to {newest_date}")
    
    # User-specific insights
    for user_id in processed_data['user_information']:
        user_prefs = len(processed_data['preferences'][user_id])
        user_projects = len(processed_data['project_context'][user_id])
        
        if user_prefs > 5:
            insights.append(f"User {user_id} has well-documented preferences ({user_prefs} entries)")
        
        if user_projects > 3:
            insights.append(f"User {user_id} is actively tracking multiple projects ({user_projects} contexts)")
    
    return insights

def main():
    """Main function to generate cognition analysis"""
    print("🔄 Starting cognition analysis...")
    
    # Fetch all memory data
    memories = fetch_all_memory_data()
    
    if not memories:
        print("❌ No memory data found in database")
        return
    
    print(f"📊 Found {len(memories)} memory entries")
    
    # Process the data
    processed_data = process_memory_data(memories)
    
    # Generate cognition.md
    generate_cognition_md(processed_data)
    
    print("✅ Cognition analysis completed successfully")

if __name__ == "__main__":
    main()
