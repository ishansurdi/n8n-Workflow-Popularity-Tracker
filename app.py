"""
My final year project - n8n Workflow Tracker
Collects popular workflow data from different platforms
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
import logging
from typing import Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Data collectors
from collectors.youtube_collector import YouTubeCollector
from collectors.forum_collector import ForumCollector
from collectors.google_collector import GoogleTrendsCollector

app = Flask(__name__)
CORS(app)

# Simple logging for development
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/n8n_workflows')
client = MongoClient(MONGODB_URI)
db = client.get_database()
workflows_collection = db.workflows
collection_history = db.collection_history

def init_db():
    """Initialize MongoDB database with indexes"""
    try:
        # Create indexes for better performance
        workflows_collection.create_index([('platform', ASCENDING)])
        workflows_collection.create_index([('country', ASCENDING)])
        workflows_collection.create_index([('engagement_score', DESCENDING)])

        
        collection_history.create_index([('timestamp', DESCENDING)])
        collection_history.create_index([('platform', ASCENDING)])
        
        logger.info("MongoDB database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

def calculate_engagement_score(workflow: Dict) -> float:
    """Calculate unified engagement score across platforms"""
    platform = workflow.get('platform', '')
    
    if platform == 'YouTube':
        views = workflow.get('views', 0)
        likes = workflow.get('likes', 0)
        comments = workflow.get('comments', 0)
        if views > 0:
            # Weighted engagement: views (40%), likes (40%), comments (20%)
            return (views * 0.0001) + (likes * 0.4) + (comments * 0.2)
    
    elif platform == 'Forum':
        views = workflow.get('views', 0)
        replies = workflow.get('replies', 0)
        likes = workflow.get('likes', 0)
        contributors = workflow.get('contributors', 0)
        # Forum engagement: replies (40%), likes (30%), contributors (20%), views (10%)
        return (replies * 40) + (likes * 30) + (contributors * 20) + (views * 0.01)
    
    elif platform == 'Google Trends':
        search_volume = workflow.get('search_volume', 0)
        trend_change = workflow.get('trend_change', 0)
        # Google: search volume (70%) + trend momentum (30%)
        return (search_volume * 0.7) + (max(0, trend_change) * 300)
    
    return 0.0

def save_workflow(workflow: Dict):
    """Save or update workflow in MongoDB"""
    try:
        # Calculate engagement score
        workflow['engagement_score'] = calculate_engagement_score(workflow)
        
        # Set timestamps
        workflow['last_updated'] = datetime.now(timezone.utc)
        
        # Check if workflow exists
        existing = workflows_collection.find_one({
            'workflow': workflow['workflow'],
            'platform': workflow['platform'],
            'country': workflow['country']
        })
        
        if existing:
            # Update existing workflow
            workflow['created_at'] = existing.get('created_at', workflow['last_updated'])
            workflows_collection.update_one(
                {'_id': existing['_id']},
                {'$set': workflow}
            )
        else:
            # Insert new workflow
            workflow['created_at'] = workflow['last_updated']
            workflows_collection.insert_one(workflow)
            
    except Exception as e:
        logger.error(f"Error saving workflow: {str(e)}")

def log_collection(platform: str, count: int, status: str, error: str = None):
    """Log collection history in MongoDB"""
    try:
        log_entry = {
            'platform': platform,
            'workflows_collected': count,
            'status': status,
            'error_message': error,
            'timestamp': datetime.now(timezone.utc)
        }
        collection_history.insert_one(log_entry)
        
    except Exception as e:
        logger.error(f"Error logging collection: {str(e)}")

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get all workflows with filtering and sorting"""
    try:
        platform = request.args.get('platform', 'all')
        country = request.args.get('country', 'all')
        sort_by = request.args.get('sort', 'engagement')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build MongoDB filter
        filter_query = {}
        
        if platform != 'all':
            filter_query['platform'] = platform
        
        if country != 'all':
            filter_query['country'] = country
        
        # Sorting
        sort_column = {
            'engagement': 'engagement_score',
            'views': 'views',
            'likes': 'likes',
            'recent': 'last_updated'
        }.get(sort_by, 'engagement_score')
        
        # Execute MongoDB query
        cursor = workflows_collection.find(filter_query).sort(sort_column, DESCENDING).skip(offset).limit(limit)
        rows = list(cursor)
        
        workflows = []
        for row in rows:
            # Handle datetime serialization
            last_updated = row.get('last_updated', '')
            if hasattr(last_updated, 'isoformat'):
                last_updated = last_updated.isoformat()
            elif last_updated:
                last_updated = str(last_updated)
                
            workflow = {
                'id': str(row['_id']),
                'workflow': row['workflow_name'],
                'platform': row['platform'],
                'country': row['country'],
                'popularity_metrics': {},
                'engagement_score': row.get('engagement_score', 0),
                'source_url': row.get('source_url', ''),
                'last_updated': last_updated
            }
            
            # Platform-specific metrics
            if row['platform'] == 'YouTube':
                workflow['popularity_metrics'] = {
                    'views': row.get('views', 0),
                    'likes': row.get('likes', 0),
                    'comments': row.get('comments', 0),
                    'like_to_view_ratio': round(row.get('like_to_view_ratio', 0), 4),
                    'comment_to_view_ratio': round(row.get('comment_to_view_ratio', 0), 4)
                }
            elif row['platform'] == 'Forum':
                workflow['popularity_metrics'] = {
                    'views': row.get('views', 0),
                    'replies': row.get('replies', 0),
                    'likes': row.get('likes', 0),
                    'contributors': row.get('contributors', 0)
                }
            elif row['platform'] == 'Google Trends':
                workflow['popularity_metrics'] = {
                    'search_volume': row.get('search_volume', 0),
                    'trend_change': round(row.get('trend_change', 0), 2)
                }
            
            workflows.append(workflow)
        
        # Get total count using MongoDB count_documents
        total = workflows_collection.count_documents(filter_query)
        
        return jsonify({
            'success': True,
            'total': total,
            'count': len(workflows),
            'workflows': workflows
        })
    
    except Exception as e:
        logger.error(f"Error fetching workflows: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get platform and country statistics"""
    try:
        # Overall stats
        total = workflows_collection.count_documents({})
        
        # Platform breakdown using aggregation
        platform_pipeline = [
            {
                '$group': {
                    '_id': '$platform',
                    'count': {'$sum': 1},
                    'avg_engagement': {'$avg': '$engagement_score'}
                }
            },
            {'$sort': {'count': -1}}
        ]
        platforms = [{
            'platform': doc['_id'],
            'count': doc['count'],
            'avg_engagement': doc.get('avg_engagement', 0)
        } for doc in workflows_collection.aggregate(platform_pipeline)]
        
        # Country breakdown
        country_pipeline = [
            {
                '$group': {
                    '_id': '$country',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]
        countries = [{
            'country': doc['_id'],
            'count': doc['count']
        } for doc in workflows_collection.aggregate(country_pipeline)]
        
        # Top workflows by engagement
        top_workflows_cursor = workflows_collection.find(
            {},
            {'workflow_name': 1, 'platform': 1, 'engagement_score': 1, '_id': 0}
        ).sort('engagement_score', DESCENDING).limit(10)
        top_workflows = list(top_workflows_cursor)
        
        # Recent collection history
        recent_collections_cursor = collection_history.find(
            {},
            {'_id': 0}
        ).sort('timestamp', DESCENDING).limit(5)
        recent_collections = list(recent_collections_cursor)
        
        return jsonify({
            'success': True,
            'total_workflows': total,
            'platforms': platforms,
            'countries': countries,
            'top_workflows': top_workflows,
            'recent_collections': recent_collections
        })
    
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/collect', methods=['POST'])
def trigger_collection():
    """Manually trigger data collection"""
    try:
        data = request.get_json()
        platforms = data.get('platforms', ['youtube', 'forum', 'google'])
        countries = data.get('countries', ['US', 'IN'])
        
        results = {
            'success': True,
            'collections': []
        }
        
        # YouTube collection
        if 'youtube' in platforms:
            try:
                youtube = YouTubeCollector(api_key=os.getenv('YOUTUBE_API_KEY'))
                for country in countries:
                    workflows = youtube.collect_workflows(country=country)
                    for wf in workflows:
                        save_workflow(wf)
                    results['collections'].append({
                        'platform': 'YouTube',
                        'country': country,
                        'count': len(workflows)
                    })
                log_collection('YouTube', len(workflows), 'success')
            except Exception as e:
                logger.error(f"YouTube collection error: {str(e)}")
                log_collection('YouTube', 0, 'error', str(e))
                results['collections'].append({
                    'platform': 'YouTube',
                    'error': str(e)
                })
        
        # Forum collection
        if 'forum' in platforms:
            try:
                forum = ForumCollector()
                workflows = forum.collect_workflows()
                for wf in workflows:
                    save_workflow(wf)
                results['collections'].append({
                    'platform': 'Forum',
                    'count': len(workflows)
                })
                log_collection('Forum', len(workflows), 'success')
            except Exception as e:
                logger.error(f"Forum collection error: {str(e)}")
                log_collection('Forum', 0, 'error', str(e))
                results['collections'].append({
                    'platform': 'Forum',
                    'error': str(e)
                })
        
        # Google Trends collection
        if 'google' in platforms:
            try:
                google = GoogleTrendsCollector()
                for country in countries:
                    workflows = google.collect_workflows(country=country)
                    for wf in workflows:
                        save_workflow(wf)
                    results['collections'].append({
                        'platform': 'Google',
                        'country': country,
                        'count': len(workflows)
                    })
                log_collection('Google', len(workflows), 'success')
            except Exception as e:
                logger.error(f"Google collection error: {str(e)}")
                log_collection('Google', 0, 'error', str(e))
                results['collections'].append({
                    'platform': 'Google',
                    'error': str(e)
                })
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Collection error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        client.admin.command('ping')
        database_status = True
    except Exception:
        database_status = False
        
    return jsonify({
        'status': 'healthy' if database_status else 'unhealthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database_connected': database_status,
        'mongodb_uri': MONGODB_URI.split('@')[1] if '@' in MONGODB_URI else 'localhost'
    })

@app.route('/')
def index():
    """Serve frontend"""
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    # Use PORT from environment for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)