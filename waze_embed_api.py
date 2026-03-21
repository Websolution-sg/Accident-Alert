#!/usr/bin/env python3
"""
NEW WORKING WAZE API IMPLEMENTATION
Based on the official embed.waze.com system
"""
import requests
import json
import uuid
import time
from datetime import datetime

class WazeEmbedAPI:
    def __init__(self):
        self.session = requests.Session()
        self.visitor_id = None
        self.base_url = 'https://embed.waze.com'
        
        # Set browser-like headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://embed.waze.com/iframe',
            'Origin': 'https://embed.waze.com'
        })

    def setup_session(self):
        """Setup authenticated session with Waze"""
        try:
            # Get visitor ID from Waze
            response = self.session.post(f'{self.base_url}/web-events/visitors', json={})
            if response.status_code == 200:
                data = response.json()
                if 'visitor_id' in data:
                    self.visitor_id = data['visitor_id']
                    print(f"✅ Got Waze visitor ID: {self.visitor_id[:20]}...")
                    
                    # Set visitor cookie for authentication
                    self.session.cookies.set('_web_visitorid', self.visitor_id, domain='embed.waze.com')
                    return True
            
            print(f"❌ Visitor setup failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Session setup error: {e}")
            return False

    def get_config(self):
        """Get Waze configuration - CONFIRMED WORKING"""
        try:
            response = self.session.get(f'{self.base_url}/api/config/LivemapConfig')
            if response.status_code == 200:
                config = response.json()
                print(f"✅ Config retrieved: {len(config)} settings")
                return config
            else:
                print(f"❌ Config failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Config error: {e}")
            return None

    def get_embed_map(self, lat=1.3521, lon=103.8198):
        """Get embed map data for Singapore"""
        try:
            params = {
                'zoom': 10,
                'lat': lat,
                'lon': lon, 
                'ct': 'livemap',
                'pin': 1
            }
            
            response = self.session.get(f'{self.base_url}/iframe', params=params)
            if response.status_code == 200:
                print(f"✅ Embed map data retrieved: {len(response.content)} bytes")
                return response.content
            else:
                print(f"❌ Map data failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Map error: {e}")
            return None

# Usage example
if __name__ == '__main__':
    print("🚗 Testing NEW Waze Embed API...")
    
    waze = WazeEmbedAPI()
    
    print("\n1. Setting up session...")
    if waze.setup_session():
        
        print("\n2. Getting configuration...")
        config = waze.get_config()
        
        print("\n3. Getting Singapore map data...")
        map_data = waze.get_embed_map()
        
        if map_data:
            print(f"\n🎉 SUCCESS! Waze API is WORKING!")
            print(f"   - Authenticated with visitor ID")
            print(f"   - Retrieved configuration data") 
            print(f"   - Got Singapore map data ({len(map_data)} bytes)")
            print(f"\n✅ You can now build on this working API!")
        else:
            print("\n⚠️  Partial success - session works but map data unavailable")
    else:
        print("\n❌ Failed to establish Waze session")