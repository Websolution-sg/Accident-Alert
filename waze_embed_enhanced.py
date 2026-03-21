#!/usr/bin/env python3
"""
ENHANCED WAZE EMBED MONITOR with improved parsing logic
"""
import requests
import json
import time
import datetime
import os
import re
import uuid
from datetime import timezone

# Configuration
BOT_TOKEN = '8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ'
CHAT_ID = '-1003683261194'
SGT = timezone(datetime.timedelta(hours=8))

SINGAPORE_BOUNDS = {
    'north': 1.4784, 'south': 1.1496, 'east': 104.0853, 'west': 103.6065        
}

CHECK_INTERVAL_SECONDS = 120  # 2 minutes
PROCESSED_FILE = 'processed_embed_accidents.json'

def log_message(message):
    timestamp = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')    
    print(f'[{timestamp}] EMBED: {message}', flush=True)

class EnhancedWazeAPI:
    def __init__(self):
        self.session = requests.Session()
        self.visitor_id = None
        self.base_url = 'https://embed.waze.com'

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://embed.waze.com/iframe',
            'Origin': 'https://embed.waze.com'
        })

    def setup_session(self):
        try:
            response = self.session.post(f'{self.base_url}/web-events/visitors', json={})
            if response.status_code in [200, 201]:
                data = response.json() if response.text else {}
                visitor_id = data.get('visitor_id', str(uuid.uuid4()))
                self.visitor_id = visitor_id
                log_message(f'✅ Authenticated with Waze: {visitor_id[:20]}...')
                self.session.cookies.set('_web_visitorid', visitor_id, domain='embed.waze.com')
                return True
            log_message(f'❌ Authentication failed: {response.status_code}')      
            return False
        except Exception as e:
            log_message(f'❌ Session setup error: {e}')
            return False

    def get_traffic_data(self):
        try:
            # Enhanced parameters for better incident detection
            params = {
                'pin': '0',
                'desc': '1',  # Enable descriptions
                'reports': '1',  # Enable reports
                'alertTypes': 'accidents,hazards,police,traffic',  # All alert types
                'width': '800',
                'height': '600',
                'lat': '1.3521',  # Singapore center
                'lon': '103.8198',
                'zoom': '11.5',  # Good detail level
                'layer': 'traffic',  # Traffic layer
                'alerts': '1'  # Enable alerts
            }
            
            response = self.session.get(f'{self.base_url}/iframe', params=params)
            if response.status_code == 200:
                return self.parse_advanced_traffic_data(response.text)
            else:
                log_message(f'❌ Traffic data failed: {response.status_code}')    
                return []
        except Exception as e:
            log_message(f'❌ Traffic data error: {e}')
            return []

    def parse_advanced_traffic_data(self, html_content):
        """Enhanced parsing to find real incident data"""
        try:
            alerts = []
            
            # Method 1: Look for JSON data structures containing alerts/incidents
            json_patterns = re.findall(r'(\{[^{}]*(?:"(?:alert|incident|accident|reports|traffic)")[^{}]*\})', html_content, re.IGNORECASE)
            
            for json_str in json_patterns:
                try:
                    # Clean and parse JSON
                    cleaned_json = json_str.strip()
                    data = json.loads(cleaned_json)
                    
                    # Check if this contains location data
                    if self.extract_incidents_from_json(data, alerts):
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Method 2: Look for JavaScript variable assignments with traffic data
            js_var_patterns = re.findall(r'var\s+(\w+)\s*=\s*(\{.*?\});', html_content, re.DOTALL)
            for var_name, var_value in js_var_patterns:
                if any(keyword in var_name.lower() for keyword in ['alert', 'incident', 'traffic', 'report']):
                    try:
                        data = json.loads(var_value)
                        self.extract_incidents_from_json(data, alerts)
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Method 3: Look for data attributes in HTML elements
            data_attr_patterns = re.findall(r'data-[^=]*=["\'](.*?)["\']', html_content)
            for attr_data in data_attr_patterns:
                if 'lat' in attr_data and 'lon' in attr_data:
                    try:
                        # Try to parse as JSON
                        data = json.loads(attr_data.replace('&quot;', '"'))
                        self.extract_incidents_from_json(data, alerts)
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Method 4: Enhanced coordinate pattern matching with context
            self.parse_contextual_coordinates(html_content, alerts)
            
            log_message(f'🔍 Enhanced parsing found {len(alerts)} potential incidents')
            return alerts[:10]  # Limit results
            
        except Exception as e:
            log_message(f'❌ Enhanced parsing error: {e}')
            return []

    def extract_incidents_from_json(self, data, alerts):
        """Extract incident information from JSON data structures"""
        try:
            if isinstance(data, dict):
                # Look for common incident data patterns
                if 'location' in data or ('lat' in data and 'lon' in data) or ('x' in data and 'y' in data):
                    lat = data.get('lat') or data.get('y') or (data.get('location', {}).get('lat'))
                    lon = data.get('lon') or data.get('x') or (data.get('location', {}).get('lon'))
                    
                    if lat and lon and self.is_within_singapore(float(lat), float(lon)):
                        alert_type = data.get('type', data.get('alertType', 'UNKNOWN'))
                        description = data.get('description', data.get('street', 'Traffic incident detected'))
                        
                        alert = {
                            'type': alert_type,
                            'street': description,
                            'location': {'y': float(lat), 'x': float(lon)},
                            'reportBy': 'Enhanced Waze Parser',
                            'confidence': data.get('confidence', 7),
                            'reliability': data.get('reliability', 7),
                            'pubMillis': data.get('pubMillis', int(time.time() * 1000)),
                            'raw_data': json.dumps(data)[:200]  # Keep sample of raw data
                        }
                        alerts.append(alert)
                        return True
                
                # Recursively search in nested objects
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        self.extract_incidents_from_json(value, alerts)
                        
            elif isinstance(data, list):
                for item in data:
                    self.extract_incidents_from_json(item, alerts)
                    
        except (ValueError, TypeError, KeyError):
            pass
            
        return False

    def parse_contextual_coordinates(self, html_content, alerts):
        """Look for coordinates with accident/incident context"""
        # More sophisticated pattern matching
        context_patterns = [
            r'(?:accident|incident|alert|hazard|crash|collision)[^0-9]*([12]\.\d{4,6})[^0-9]*(103\.\d{4,6})',
            r'([12]\.\d{4,6})[^0-9]*(103\.\d{4,6})[^0-9]*(?:accident|incident|alert|hazard|crash|collision)',
            r'"type"[^"]+"accident"[^0-9]*([12]\.\d{4,6})[^0-9]*(103\.\d{4,6})',
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for lat_str, lon_str in matches:
                try:
                    lat, lon = float(lat_str), float(lon_str)
                    if self.is_within_singapore(lat, lon):
                        alert = {
                            'type': 'ACCIDENT',
                            'street': 'Contextual incident detected',
                            'location': {'y': lat, 'x': lon},
                            'reportBy': 'Enhanced Context Parser',
                            'confidence': 6,
                            'reliability': 6,
                            'pubMillis': int(time.time() * 1000)
                        }
                        alerts.append(alert)
                except ValueError:
                    continue

    def is_within_singapore(self, lat, lon):
        """Check if coordinates are within Singapore bounds"""
        return (SINGAPORE_BOUNDS['south'] <= lat <= SINGAPORE_BOUNDS['north'] and                
                SINGAPORE_BOUNDS['west'] <= lon <= SINGAPORE_BOUNDS['east'])    

def load_processed():
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()

def save_processed(processed):
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed), f)
    except Exception as e:
        log_message(f'❌ Error saving processed: {e}')

def get_accident_id(alert):
    """Generate unique ID for incident deduplication"""
    if alert.get('location'):
        lat = alert['location'].get('y', 0)
        lon = alert['location'].get('x', 0)
        time_hour = datetime.datetime.now().strftime('%Y%m%d_%H')
        return f'enhanced_{lat:.3f}_{lon:.3f}_{time_hour}'
    return f'enhanced_unknown_{int(time.time())}'

def send_telegram_message(message):
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown',      
            'disable_web_page_preview': True
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        log_message(f'❌ Telegram error: {e}')
        return False

def format_message(alert):
    """Format incident message for Telegram"""
    location = alert.get('location', {})
    lat, lon = location.get('y', 0), location.get('x', 0)
    street = alert.get('street', 'Unknown location')
    alert_type = alert.get('type', 'INCIDENT')
    confidence = alert.get('confidence', 5)
    
    message = f"🚨 **{alert_type.upper()}** Alert\n\n"
    message += f"📍 **Location:** {street}\n"
    message += f"🌐 **Coordinates:** {lat:.4f}, {lon:.4f}\n"
    message += f"⭐ **Confidence:** {confidence}/10\n"
    message += f"🕒 **Time:** {datetime.datetime.now(SGT).strftime('%H:%M:%S')}\n"
    message += f"🔗 [View on Maps](https://maps.google.com/maps?q={lat},{lon})"
    
    return message

def main_monitor_loop():
    """Main monitoring loop with enhanced detection"""
    log_message('🚀 Starting Enhanced Waze Monitor for Singapore...')
    log_message(f'⏱️ Check interval: {CHECK_INTERVAL_SECONDS} seconds')
    
    api = EnhancedWazeAPI()
    processed = load_processed()
    
    while True:
        try:
            # Setup/refresh session
            if not api.setup_session():
                log_message('❌ Session setup failed, retrying in 60s...')
                time.sleep(60)
                continue
            
            # Get traffic data
            alerts = api.get_traffic_data()
            
            if alerts:
                new_count = 0
                for alert in alerts:
                    alert_id = get_accident_id(alert)
                    if alert_id not in processed:
                        message = format_message(alert)
                        if send_telegram_message(message):
                            processed.add(alert_id)
                            new_count += 1
                            log_message(f'✅ Posted new enhanced incident: {alert_id}')        
                            time.sleep(2)  # Rate limiting
                
                if new_count > 0:
                    save_processed(processed)
                    log_message(f'📨 Sent {new_count} new incident(s)')
                else:
                    log_message('🔍 No new incidents (all already processed)')
            else:
                log_message('❓ No incidents detected')
            
            log_message(f'⏱️ Waiting {CHECK_INTERVAL_SECONDS}s until next check...')
            time.sleep(CHECK_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            log_message('🛑 Monitor stopped by user')
            break
        except Exception as e:
            log_message(f'❌ Monitor error: {e}')
            time.sleep(30)  # Brief pause on errors

if __name__ == '__main__':
    main_monitor_loop()