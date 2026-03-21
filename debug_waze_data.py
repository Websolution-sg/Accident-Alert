#!/usr/bin/env python3
import requests
import json
import re
from datetime import datetime

class WazeDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://embed.waze.com/iframe'
        })

    def authenticate(self):
        try:
            response = self.session.post('https://embed.waze.com/web-events/visitors', json={})
            if response.status_code in [200, 201]:
                data = response.json() if response.text else {}
                visitor_id = data.get('visitor_id', 'auth_token')
                print(f'✅ Authentication: {response.status_code}')
                if visitor_id:
                    self.session.cookies.set('_web_visitorid', visitor_id, domain='embed.waze.com')
                return True
            print(f'❌ Auth failed: {response.status_code}')
            return False
        except Exception as e:
            print(f'❌ Auth error: {e}')
            return False

    def analyze_embed_content(self):
        """Analyze actual Waze embed content structure"""
        try:
            # Get Singapore embed with all alert types
            params = {
                'pin': '0', 'desc': '0', 'reports': '1', 
                'alertTypes': 'accidents,hazards,police,traffic',
                'width': '800', 'height': '600',
                'lat': '1.3521', 'lon': '103.8198', 
                'zoom': '11.5'
            }
            
            url = 'https://embed.waze.com/iframe'
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                content = response.text
                print(f'✅ Content retrieved: {len(content)} chars')
                
                # Save raw content for analysis
                with open('waze_raw_content.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Analyze structure
                self.analyze_structure(content)
                return content
            else:
                print(f'❌ Content failed: {response.status_code}')
                return None
                
        except Exception as e:
            print(f'❌ Content error: {e}')
            return None

    def analyze_structure(self, content):
        """Analyze the HTML structure for incident data"""
        print("\n🔍 ANALYZING WAZE EMBED STRUCTURE...")
        
        # Check for JSON objects
        json_patterns = re.finditer(r'{[^{}]*(?:{[^{}]*}[^{}]*)*}', content)
        json_count = 0
        for match in json_patterns:
            json_count += 1
            if json_count <= 3:  # Show first 3 JSON objects
                print(f"\n📋 JSON Object {json_count}:")
                json_text = match.group(0)[:200] + ('...' if len(match.group(0)) > 200 else '')
                print(json_text)
        
        # Look for accident-related keywords
        keywords = ['accident', 'incident', 'alert', 'report', 'hazard', 'traffic']
        for keyword in keywords:
            matches = len(re.findall(keyword, content, re.IGNORECASE))
            if matches > 0:
                print(f"🎯 '{keyword}': {matches} occurrences")
        
        # Check for coordinate patterns
        coord_patterns = re.findall(r'[12]\.[0-9]{4,6}.*?10[34]\.[0-9]{4,6}', content)
        print(f"📍 Coordinate patterns found: {len(coord_patterns)}")
        if coord_patterns:
            for i, pattern in enumerate(coord_patterns[:3]):
                print(f"  {i+1}: {pattern[:100]}...")
        
        # Look for JavaScript variables
        js_vars = re.findall(r'var\s+(\w+)\s*=\s*({.*?});', content, re.DOTALL)
        print(f"⚙️ JavaScript variables: {len(js_vars)}")
        for var_name, var_value in js_vars[:3]:
            print(f"  {var_name}: {var_value[:100]}...")

if __name__ == '__main__':
    print('🔧 DEBUGGING WAZE EMBED STRUCTURE')
    debugger = WazeDebugger()
    
    if debugger.authenticate():
        content = debugger.analyze_embed_content()
        if content:
            print('\n✅ Analysis complete. Check waze_raw_content.html for full content.')
        else:
            print('❌ Failed to get content')
    else:
        print('❌ Authentication failed')