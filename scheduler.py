"""
Data collection scheduler - runs daily to get fresh workflow data
Part of my college project on n8n workflow analysis
"""

import schedule
import time
import logging
from datetime import datetime, timezone
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collectors.youtube_collector import YouTubeCollector
from collectors.forum_collector import ForumCollector
from collectors.google_collector import GoogleTrendsCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/n8n_workflows')
client = MongoClient(MONGODB_URI)
db = client.get_database()
workflows_collection = db.workflows
collection_history = db.collection_history

def calculate_engagement_score(workflow):
    """Calculate unified engagement score"""
    platform = workflow.get('platform', '')
    
    if platform == 'YouTube':
        views = workflow.get('views', 0)
        likes = workflow.get('likes', 0)
        comments = workflow.get('comments', 0)
        if views > 0:
            return (views * 0.0001) + (likes * 0.4) + (comments * 0.2)
    
    elif platform == 'Forum':
        views = workflow.get('views', 0)
        replies = workflow.get('replies', 0)
        likes = workflow.get('likes', 0)
        contributors = workflow.get('contributors', 0)
        return (replies * 40) + (likes * 30) + (contributors * 20) + (views * 0.01)
    
    elif platform == 'Google':
        search_volume = workflow.get('search_volume', 0)
        trend_change = workflow.get('trend_change', 0)
        return (search_volume * 0.7) + (max(0, trend_change) * 300)
    
    return 0.0

def save_workflow(workflow):
    """Save workflow to MongoDB"""
    try:
        workflow['engagement_score'] = calculate_engagement_score(workflow)
        workflow['last_updated'] = datetime.now(timezone.utc)
        
        # Check if workflow exists
        existing = workflows_collection.find_one({
            'workflow_name': workflow['workflow_name'],
            'platform': workflow['platform'],
            'country': workflow['country']
        })
        
        if existing:
            # Update existing workflow
            workflows_collection.update_one(
                {'_id': existing['_id']},
                {
                    '$set': {
                        'views': workflow.get('views', 0),
                        'likes': workflow.get('likes', 0),
                        'comments': workflow.get('comments', 0),
                        'replies': workflow.get('replies', 0),
                        'contributors': workflow.get('contributors', 0),
                        'search_volume': workflow.get('search_volume', 0),
                        'trend_change': workflow.get('trend_change', 0.0),
                        'like_to_view_ratio': workflow.get('like_to_view_ratio', 0.0),
                        'comment_to_view_ratio': workflow.get('comment_to_view_ratio', 0.0),
                        'engagement_score': workflow['engagement_score'],
                        'source_url': workflow.get('source_url', ''),
                        'last_updated': workflow['last_updated']
                    }
                }
            )
        else:
            # Insert new workflow
            workflow['created_at'] = datetime.now(timezone.utc)
            workflows_collection.insert_one(workflow)
            
    except Exception as e:
        logger.error(f"Error saving workflow: {str(e)}")

def log_collection(platform, count, status, error=None):
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

def collect_youtube_data():
    """Collect YouTube workflow data"""
    logger.info("Starting YouTube data collection")
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        logger.error("YOUTUBE_API_KEY not set")
        log_collection('YouTube', 0, 'error', 'API key not set')
        return
    
    try:
        collector = YouTubeCollector(api_key=api_key)
        total_count = 0
        
        for country in ['US', 'IN']:
            workflows = collector.collect_workflows(country=country)
            for wf in workflows:
                save_workflow(wf)
            total_count += len(workflows)
            logger.info(f"Collected {len(workflows)} YouTube workflows for {country}")
        
        log_collection('YouTube', total_count, 'success')
        logger.info(f"YouTube collection completed. Total: {total_count}")
    
    except Exception as e:
        logger.error(f"YouTube collection failed: {str(e)}")
        log_collection('YouTube', 0, 'error', str(e))

def collect_forum_data():
    """Collect Forum workflow data"""
    logger.info("Starting Forum data collection")
    
    try:
        collector = ForumCollector()
        workflows = collector.collect_workflows()
        
        for wf in workflows:
            save_workflow(wf)
        
        log_collection('Forum', len(workflows), 'success')
        logger.info(f"Forum collection completed. Total: {len(workflows)}")
    
    except Exception as e:
        logger.error(f"Forum collection failed: {str(e)}")
        log_collection('Forum', 0, 'error', str(e))

def collect_google_data():
    """Collect Google Trends data"""
    logger.info("Starting Google Trends collection")
    
    try:
        collector = GoogleTrendsCollector()
        total_count = 0
        
        for country in ['US', 'IN']:
            workflows = collector.collect_workflows(country=country)
            for wf in workflows:
                save_workflow(wf)
            total_count += len(workflows)
            logger.info(f"Collected {len(workflows)} Google Trends for {country}")
        
        log_collection('Google', total_count, 'success')
        logger.info(f"Google Trends collection completed. Total: {total_count}")
    
    except Exception as e:
        logger.error(f"Google Trends collection failed: {str(e)}")
        log_collection('Google', 0, 'error', str(e))

def run_daily_collection():
    """Run complete daily collection"""
    logger.info("=" * 50)
    logger.info(f"Starting daily collection at {datetime.now()}")
    logger.info("=" * 50)
    
    collect_youtube_data()
    time.sleep(5)  # Rate limiting between platforms
    
    collect_forum_data()
    time.sleep(5)
    
    collect_google_data()
    
    logger.info("=" * 50)
    logger.info("Daily collection completed")
    logger.info("=" * 50)

def main():
    """Main scheduler loop"""
    logger.info("n8n Workflow Scheduler started")
    
    # Run immediately on startup
    run_daily_collection()
    
    # Schedule daily at 2 AM
    schedule.every().day.at("02:00").do(run_daily_collection)
    
    # Alternative: Run every 6 hours
    # schedule.every(6).hours.do(run_daily_collection)
    
    logger.info("Scheduler configured. Running daily at 02:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")