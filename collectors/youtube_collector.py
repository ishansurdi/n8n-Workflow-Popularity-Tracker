"""
YouTube data collector - gets n8n workflow videos
Using YouTube API to find popular videos
"""

import requests
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class YouTubeCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        
        # n8n workflow related search queries
        self.search_queries = [
            'n8n automation workflow',
            'n8n tutorial',
            'n8n integration',
            'n8n slack automation',
            'n8n google sheets',
            'n8n airtable',
            'n8n webhook',
            'n8n discord bot',
            'n8n telegram bot',
            'n8n gmail automation',
            'n8n notion integration',
            'n8n api workflow',
            'n8n schedule automation',
            'n8n data sync',
            'n8n crm automation',
            'n8n email automation',
            'n8n database workflow',
            'n8n scraping',
            'n8n twitter automation',
            'n8n instagram automation'
        ]
    
    def search_videos(self, query: str, country: str = 'US', max_results: int = 50) -> List[Dict]:
        """Search for n8n related videos"""
        try:
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'regionCode': country,
                'relevanceLanguage': 'en',
                'key': self.api_key,
                'order': 'viewCount'
            }
            
            response = requests.get(f'{self.base_url}/search', params=params)
            response.raise_for_status()
            data = response.json()
            
            video_ids = [item['id']['videoId'] for item in data.get('items', [])]
            
            if not video_ids:
                return []
            
            # Get video statistics
            return self.get_video_details(video_ids, country)
        
        except Exception as e:
            logger.error(f"Error searching YouTube for '{query}': {str(e)}")
            return []
    
    def get_video_details(self, video_ids: List[str], country: str) -> List[Dict]:
        """Get detailed statistics for videos"""
        try:
            params = {
                'part': 'snippet,statistics',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            
            response = requests.get(f'{self.base_url}/videos', params=params)
            response.raise_for_status()
            data = response.json()
            
            workflows = []
            for item in data.get('items', []):
                snippet = item['snippet']
                stats = item['statistics']
                
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                # Calculate ratios
                like_ratio = likes / views if views > 0 else 0
                comment_ratio = comments / views if views > 0 else 0
                
                workflow = {
                    'workflow_name': snippet['title'][:200],  # Limit length
                    'platform': 'YouTube',
                    'country': country,
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'like_to_view_ratio': like_ratio,
                    'comment_to_view_ratio': comment_ratio,
                    'source_url': f"https://www.youtube.com/watch?v={item['id']}"
                }
                
                workflows.append(workflow)
            
            return workflows
        
        except Exception as e:
            logger.error(f"Error getting video details: {str(e)}")
            return []
    
    def collect_workflows(self, country: str = 'US') -> List[Dict]:
        """Collect all workflows for a country"""
        all_workflows = []
        
        logger.info(f"Starting YouTube collection for {country}")
        
        for query in self.search_queries:
            workflows = self.search_videos(query, country, max_results=10)
            all_workflows.extend(workflows)
            logger.info(f"Collected {len(workflows)} workflows for query: {query}")
        
        # Remove duplicates based on URL
        unique_workflows = {}
        for wf in all_workflows:
            url = wf['source_url']
            if url not in unique_workflows or wf['views'] > unique_workflows[url]['views']:
                unique_workflows[url] = wf
        
        result = list(unique_workflows.values())
        logger.info(f"Total unique YouTube workflows for {country}: {len(result)}")
        
        return result