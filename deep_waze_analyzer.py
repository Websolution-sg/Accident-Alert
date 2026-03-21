#!/usr/bin/env python3
"""
Deep debugging script to analyze Waze embed data and parsing effectiveness
"""
import requests
import json
import re
from datetime import datetime

class WazeDataAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://embed.waze.com/iframe',
            'Origin': 'https://embed.waze.com'
        })

    def authenticate(self):
        try:
            response = self.session.post('https://embed.waze.com/web-events/visitors', json={})
            if response.status_code in [200, 201]:
                data = response.json() if response.text else {}
                visitor_id = data.get('visitor_id', 'fallback_token')
                print(f"✅ Authentication: {response.status_code}")
                if visitor_id:
                    self.session.cookies.set('_web_visitorid', visitor_id, domain='embed.waze.com')
                return True
            print(f"❌ Auth failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False

    def deep_analyze_waze_data(self):
        """Perform deep analysis of Waze embed data"""
        try:
            # Test multiple parameter combinations to see what works best
            param_sets = [
                # Set 1: Current parameters
                {
                    'pin': '0', 'desc': '1', 'reports': '1', 
                    'alertTypes': 'accidents,hazards,police,traffic',
                    'width': '800', 'height': '600',
                    'lat': '1.3521', 'lon': '103.8198', 'zoom': '11.5'
                },
                # Set 2: Minimal parameters
                {
                    'lat': '1.3521', 'lon': '103.8198', 'zoom': '12'
                },
                # Set 3: Focus on accidents only
                {
                    'lat': '1.3521', 'lon': '103.8198', 'zoom': '11',
                    'alertTypes': 'accidents', 'reports': '1'
                }
            ]

            print("🔍 DEEP WAZE DATA ANALYSIS")
            print("=" * 50)

            for i, params in enumerate(param_sets, 1):
                print(f"\n📊 Parameter Set {i}: {params}")
                
                response = self.session.get('https://embed.waze.com/iframe', params=params)
                
                if response.status_code == 200:
                    content = response.text
                    print(f"✅ Response: {len(content)} chars")
                    
                    # Save sample for manual inspection
                    with open(f'waze_sample_{i}.html', 'w', encoding='utf-8') as f:
                        f.write(content[:10000])  # First 10K chars
                    
                    # Analyze content structure
                    self.analyze_content_structure(content, f"Set {i}")
                    
                else:
                    print(f"❌ Failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Analysis error: {e}")

    def analyze_content_structure(self, content, label):
        """Analyze the structure of Waze embed content"""
        print(f"\n🔍 Analysis for {label}:")
        
        # 1. Look for obvious incident keywords
        keywords = ['accident', 'crash', 'collision', 'incident', 'alert', 'hazard', 'jam', 'traffic']
        keyword_counts = {}
        for keyword in keywords:
            count = len(re.findall(keyword, content, re.IGNORECASE))
            if count > 0:
                keyword_counts[keyword] = count
        
        if keyword_counts:
            print(f"   🎯 Keywords found: {keyword_counts}")
        else:
            print("   ❌ No relevant keywords found")

        # 2. Look for coordinate patterns
        coord_patterns = [
            r'[12]\.\d{4,6}["\s,]*103\.\d{4,6}',  # Singapore coordinates
            r'103\.\d{4,6}["\s,]*[12]\.\d{4,6}',  # Reversed
            r'"lat"[:\s]*[12]\.\d{4,6}',          # JSON lat
            r'"lon"[:\s]*103\.\d{4,6}',           # JSON lon
        ]
        
        coord_matches = 0
        for pattern in coord_patterns:
            matches = re.findall(pattern, content)
            coord_matches += len(matches)
            if matches:
                print(f"   📍 Coordinate pattern '{pattern[:20]}...': {len(matches)} matches")
                # Show samples
                for match in matches[:3]:
                    print(f"      Sample: {match}")

        if coord_matches == 0:
            print("   ❌ No coordinate patterns found")

        # 3. Look for JSON structures
        json_objects = re.findall(r'{[^{}]{10,200}}', content)
        print(f"   📋 JSON-like objects: {len(json_objects)}")
        
        # Try to parse JSON objects
        valid_json_count = 0
        for i, obj in enumerate(json_objects[:5]):  # Check first 5
            try:
                data = json.loads(obj)
                valid_json_count += 1
                if any(key in str(data).lower() for key in ['lat', 'lon', 'accident', 'alert']):
                    print(f"   ✅ Relevant JSON {i+1}: {obj[:60]}...")
            except:
                pass
        
        print(f"   📊 Valid JSON objects: {valid_json_count}")

        # 4. Look for script tags and variables
        script_vars = re.findall(r'var\s+(\w+)\s*=\s*([^;]{10,100});', content)
        relevant_vars = [(name, value) for name, value in script_vars 
                        if any(keyword in name.lower() or keyword in value.lower() 
                              for keyword in ['alert', 'incident', 'traffic', 'accident'])]
        
        if relevant_vars:
            print(f"   ⚙️ Relevant variables: {len(relevant_vars)}")
            for name, value in relevant_vars[:3]:
                print(f"      {name}: {value[:50]}...")
        else:
            print("   ❌ No relevant JavaScript variables")

        # 5. Check data attributes
        data_attrs = re.findall(r'data-[^=]*=["\'](.*?)["\']', content)
        relevant_data = [attr for attr in data_attrs if 
                        any(keyword in attr.lower() for keyword in ['lat', 'lon', 'accident', 'alert'])]
        
        if relevant_data:
            print(f"   📊 Relevant data attributes: {len(relevant_data)}")
            for attr in relevant_data[:3]:
                print(f"      {attr[:50]}...")
        else:
            print("   ❌ No relevant data attributes")

        return len(keyword_counts) > 0 or coord_matches > 0 or valid_json_count > 0

    def test_alternative_apis(self):
        """Test if there are other Waze endpoints that might work better"""
        print("\n🔄 TESTING ALTERNATIVE ENDPOINTS")
        print("=" * 40)
        
        endpoints = [
            'https://embed.waze.com/api/config/LivemapConfig',
            'https://embed.waze.com/api/events',
            'https://embed.waze.com/api/reports',
            'https://embed.waze.com/api/alerts'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint)
                print(f"📡 {endpoint}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    content = response.text[:200]
                    print(f"   Content preview: {content}...")
                    if 'accident' in content.lower() or 'alert' in content.lower():
                        print(f"   🎯 Contains relevant data!")
                print()
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    analyzer = WazeDataAnalyzer()
    
    if analyzer.authenticate():
        analyzer.deep_analyze_waze_data()
        analyzer.test_alternative_apis()
    else:
        print("❌ Authentication failed - cannot proceed with analysis")