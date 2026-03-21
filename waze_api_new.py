#!/usr/bin/env python3
import requests
import json
import time
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('waze_api_new.log'),
        logging.StreamHandler()
    ]
)

class WazeAPINew:
    def __init__(self):
        self.session = requests.Session()
        self.visitor_id = str(uuid.uuid4())
        self.base_url = 'https://embed.waze.com'
        
        # Set headers like the browser does
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://embed.waze.com/iframe',
            'Origin': 'https://embed.waze.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        
        # Set visitor cookie
        self.session.cookies.set('_web_visitorid', self.visitor_id, domain='embed.waze.com')
        
    def setup_visitor(self):
        """Setup visitor ID with Waze backend"""
        try:
            response = self.session.post(f'{self.base_url}/web-events/visitors', 
                                       json={}, 
                                       timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'visitor_id' in data:
                    self.visitor_id = data['visitor_id']
                    logging.info(f'Set visitor ID: {self.visitor_id}')
                    return True
            logging.warning(f'Visitor setup returned {response.status_code}')
            return False
        except Exception as e:
            logging.error(f'Failed to setup visitor: {e}')
            return False

    def get_config(self):
        """Get Waze LivemapConfig"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Visitor-Id': self.visitor_id
            }
            
            response = self.session.get(f'{self.base_url}/api/config/LivemapConfig',
                                      headers=headers, 
                                      timeout=10)
            
            logging.info(f'Config response: {response.status_code}')
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f'Config error: {response.text}')
                return None
        except Exception as e:
            logging.error(f'Config request failed: {e}')
            return None

    def get_alerts_singapore(self):
        """Attempt to get Singapore traffic alerts"""
        # Singapore bounding box
        lat_center = 1.3521
        lon_center = 103.8198
        
        # Try multiple potential endpoints
        endpoints = [
            f'/api/alerts?lat={lat_center}&lon={lon_center}&radius=25',
            f'/api/georss?lat={lat_center}&lon={lon_center}',
            f'/api/traffic?lat={lat_center}&lon={lon_center}&radius=25',
            f'/livemap-api/alerts?lat={lat_center}&lon={lon_center}',
            f'/livemap-api/georss?lat={lat_center}&lon={lon_center}'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f'{self.base_url}{endpoint}',
                                          headers={'X-Visitor-Id': self.visitor_id},
                                          timeout=10)
                logging.info(f'Alerts endpoint {endpoint}: {response.status_code}')
                
                if response.status_code == 200:
                    if response.content:
                        logging.info(f'Got data from {endpoint}!')
                        return response.content
                elif response.status_code != 404:
                    logging.info(f'Response: {response.text[:200]}...')
                    
            except Exception as e:
                logging.error(f'Failed {endpoint}: {e}')
                
        return None

def test_new_api():
    """Test the new Waze API"""
    waze = WazeAPINew()
    
    # Setup visitor
    logging.info('Setting up visitor...')
    visitor_ok = waze.setup_visitor()
    
    # Get config
    logging.info('Getting config...')
    config = waze.get_config()
    if config:
        logging.info(f'Config keys: {list(config.keys()) if isinstance(config, dict) else "Not dict"}')
    
    # Try to get alerts
    logging.info('Testing alert endpoints...')
    alerts = waze.get_alerts_singapore()
    if alerts:
        logging.info(f'Got alerts data! Length: {len(alerts)} bytes')
        # Save sample
        with open('sample_alerts.data', 'wb') as f:
            f.write(alerts)
    else:
        logging.info('No alerts data found')

if __name__ == '__main__':
    test_new_api()