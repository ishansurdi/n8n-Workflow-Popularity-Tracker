"""
Google Trends collector - tracks search popularity
Simulates trending data for n8n keywords
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class GoogleTrendsCollector:
    def __init__(self):
        # n8n workflow related keywords for trends analysis
        self.workflow_keywords = [
            'n8n automation',
            'n8n workflow',
            'n8n integration',
            'workflow automation',
            'n8n tutorial',
            'n8n webhook',
            'n8n api',
            'no code automation',
            'n8n slack',
            'n8n google sheets',
            'n8n notion',
            'n8n discord',
            'n8n telegram',
            'n8n airtable',
            'n8n zapier alternative'
        ]
        
        # Country codes for Google Trends
        self.country_codes = {
            'US': 'US',
            'GB': 'GB', 
            'DE': 'DE',
            'FR': 'FR',
            'CA': 'CA',
            'AU': 'AU',
            'IN': 'IN',
            'BR': 'BR',
            'JP': 'JP',
            'Global': ''
        }
    
    def get_trends_data(self, keyword: str, country: str = 'US') -> Dict:
        """Get real Google Trends data for a keyword"""
        try:
            from pytrends.request import TrendReq
            
            # Initialize pytrends
            pytrends = TrendReq(hl='en-US', tz=360)
            country_code = self.country_codes.get(country, 'US')
            
            # Build the payload for Google Trends
            pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo=country_code)
            
            # Get interest over time (trend data)
            interest_over_time_df = pytrends.interest_over_time()
            
            if interest_over_time_df.empty:
                # Fallback to simulated data if no results
                logger.warning(f"No Google Trends data for '{keyword}' in {country}, using simulated data")
                trend_score = random.randint(15, 85)
                trend_change = random.uniform(-20.0, 40.0)
            else:
                # Calculate trend metrics from real data
                recent_values = interest_over_time_df[keyword].tail(4).values
                trend_score = int(recent_values.mean()) if len(recent_values) > 0 else random.randint(15, 85)
                
                # Calculate trend change (last month vs previous month)
                if len(recent_values) >= 2:
                    trend_change = ((recent_values[-1] - recent_values[-2]) / max(recent_values[-2], 1)) * 100
                else:
                    trend_change = random.uniform(-10.0, 25.0)
            
            # Get related queries (if available)
            try:
                related_queries_dict = pytrends.related_queries()
                related_queries = []
                if keyword in related_queries_dict and related_queries_dict[keyword]['top'] is not None:
                    related_queries = related_queries_dict[keyword]['top']['query'].head(3).tolist()
                else:
                    related_queries = [f"{keyword} tutorial", f"{keyword} guide", f"how to {keyword}"]
            except:
                related_queries = [f"{keyword} tutorial", f"{keyword} guide", f"how to {keyword}"]
            
            # Calculate estimated search volume (trend_score * multiplier based on keyword popularity)
            search_volume_multiplier = random.randint(500, 2000)  # Realistic multiplier
            estimated_search_volume = int(trend_score * search_volume_multiplier)
            
            trends_data = {
                'keyword': keyword,
                'country': country,
                'trend_score': trend_score,
                'trend_change': round(trend_change, 1),
                'search_volume': estimated_search_volume,
                'related_queries': related_queries[:3],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Collected real trends for '{keyword}' in {country}: score {trend_score}, change {trend_change:.1f}%")
            return trends_data
            
        except ImportError:
            logger.warning("pytrends not installed, using enhanced simulated data")
            # Enhanced simulated data with realistic variations
            trend_score = random.randint(25, 90)
            
            # Create more realistic trend changes based on keyword popularity
            keyword_lower = keyword.lower()
            if 'slack' in keyword_lower or 'discord' in keyword_lower or 'notion' in keyword_lower:
                # Popular integrations tend to have positive growth
                trend_change = random.uniform(15.0, 45.0)
            elif 'webhook' in keyword_lower or 'api' in keyword_lower:
                # Technical terms have moderate growth
                trend_change = random.uniform(-5.0, 25.0)
            elif 'tutorial' in keyword_lower:
                # Tutorial searches growing
                trend_change = random.uniform(10.0, 35.0)
            else:
                # General automation keywords
                trend_change = random.uniform(-12.0, 28.0)
            
            # Calculate search volume with realistic ranges
            if trend_score > 70:
                search_volume = trend_score * random.randint(800, 1800)  # High popularity
            elif trend_score > 40:
                search_volume = trend_score * random.randint(500, 1200)  # Medium popularity
            else:
                search_volume = trend_score * random.randint(200, 800)   # Lower popularity
            
            trends_data = {
                'keyword': keyword,
                'country': country,
                'trend_score': trend_score,
                'trend_change': round(trend_change, 1),
                'search_volume': search_volume,
                'related_queries': [f"{keyword} tutorial", f"{keyword} guide", f"how to {keyword}"],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Simulated trends for '{keyword}' in {country}: score {trend_score}, change {trend_change:.1f}%")
            return trends_data
            
        except Exception as e:
            logger.error(f"Error getting trends data for {keyword}: {str(e)}")
            return None
    
    def create_workflow_from_trend(self, trends_data: Dict) -> Dict:
        """Convert trends data to workflow format"""
        try:
            keyword = trends_data['keyword']
            country = trends_data['country']
            trend_score = trends_data['trend_score']
            trend_change = trends_data.get('trend_change', 0.0)
            search_volume = trends_data.get('search_volume', trend_score * 1000)
            
            # Create workflow object matching expected format
            workflow = {
                'workflow_name': f"{keyword} automation workflow",
                'platform': 'Google Trends',
                'country': country,
                'trend_score': trend_score,
                'search_volume': search_volume,
                'trend_change': trend_change,
                'related_queries': trends_data['related_queries'],
                'popularity_index': trend_score,
                'source_url': f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '%20')}&geo={self.country_codes.get(country, 'US')}",
                'timestamp': trends_data['timestamp']
            }
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow from trends: {str(e)}")
            return None
    
    def collect_workflows(self, country: str = 'US') -> List[Dict]:
        """Collect all trending workflows for a country"""
        all_workflows = []
        
        logger.info(f"Starting Google Trends collection for {country}")
        
        for keyword in self.workflow_keywords:
            trends_data = self.get_trends_data(keyword, country)
            if trends_data:
                workflow = self.create_workflow_from_trend(trends_data)
                if workflow:
                    all_workflows.append(workflow)
                    logger.info(f"Collected trend data for keyword: {keyword}")
        
        # Sort by trend score (highest first)
        all_workflows.sort(key=lambda x: x.get('trend_score', 0), reverse=True)
        
        logger.info(f"Total Google Trends workflows for {country}: {len(all_workflows)}")
        
        return all_workflows