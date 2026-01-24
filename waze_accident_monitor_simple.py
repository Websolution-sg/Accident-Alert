"""
Waze Accident Monitor - Simple Working Version
Secondary Instance for Channel -1003683261194
"""
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Set
import os
import re

class WazeAccidentMonitor:
    def __init__(self, telegram_bot_token: str, telegram_channel_id: str):
        self.telegram_bot_token = telegram_bot_token
        self.telegram_channel_id = telegram_channel_id
        self.telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}"
        self.posted_accidents: Set[str] = set()
        self.posted_addresses: Set[str] = set()  # Track addresses from both sources
        self.waze_addresses: Set[str] = set()  # Track addresses specifically from Waze
        self.processed_messages: Set[str] = set()  # Track processed @sgaccident messages
        self.last_update_id = None  # Track last processed update ID
        
        # Singapore bounding box
        self.bbox = {
            'bottom': 1.1304753,
            'left': 103.6055424,
            'right': 104.0945619,
            'top': 1.4764671
        }
        
    def get_waze_alerts(self) -> List[Dict]:
        url = "https://www.waze.com/live-map/api/georss"
        params = {
            'bottom': self.bbox['bottom'],
            'left': self.bbox['left'],
            'right': self.bbox['right'],
            'top': self.bbox['top'],
            'env': 'row',
            'types': 'alerts'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get('alerts', [])
        except Exception as e:
            print(f"Error fetching Waze alerts: {e}")
            return []
    def get_telegram_updates(self) -> List[Dict]:
        """Get updates from Telegram API including channel posts"""
        url = f"{self.telegram_api_url}/getUpdates"
        params = {
            'timeout': 5,
            'limit': 100,
            'allowed_updates': '["channel_post"]'
        }
        
        if self.last_update_id:
            params['offset'] = self.last_update_id + 1
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                updates = data.get('result', [])
                if updates:
                    self.last_update_id = updates[-1]['update_id']
                return updates
        except Exception as e:
            print(f"Error getting Telegram updates: {e}")
        return []
    
    def extract_location_from_message(self, text: str) -> tuple:
    
    def filter_accidents(self, alerts: List[Dict]) -> List[Dict]:
        accidents = []
        for alert in alerts:
            if alert.get('type') == 'ACCIDENT':
                accidents.append(alert)
        return accidents
    
    def format_accident_message(self, accident: Dict) -> str:
        street = accident.get('street', 'Unknown location')
        lat = accident.get('location', {}).get('y', 0)
        lon = accident.get('location', {}).get('x', 0)
        
        message = f"🚨 *ACCIDENT ALERT*\n\n"
        message += f"📍 *Location:* {street}\n"
        message += f"⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}\n"
        
        if lat and lon:
            message += f"🗺️ *Google Maps:* https://maps.google.com/?q={lat},{lon}\n"
            message += f"🚗 *Waze:* https://waze.com/ul?ll={lat}%2C{lon}&navigate=yes\n"
        
        message += f"\n🔗 *Source:* Waze Live Map"
        return message
    
    def send_telegram_message(self, message: str) -> bool:
        url = f"{self.telegram_api_url}/sendMessage"
        data = {
            'chat_id': self.telegram_channel_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for duplicate detection"""
        if not address:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        
        # Remove common prefixes
        prefixes = ['accident at', 'accident along', 'at', 'along', 'near']
        for prefix in prefixes:
            if normalized.startswith(prefix + ' '):
                normalized = normalized[len(prefix):].strip()
        
        # Standardize road abbreviations
        replacements = {
            ' road': ' rd', ' avenue': ' ave', ' street': ' st',
            ' drive': ' dr', ' lane': ' ln'
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def format_sgaccident_message(self, location, coords=None) -> str:
        """Format @sgaccident message in Waze-compatible format"""
        message = f"🚨 *ACCIDENT ALERT*\n\n"
        
        if isinstance(location, tuple):  # coordinates
            lat, lon = location
            message += f"📍 *Location:* {lat:.4f}, {lon:.4f}\n"
        else:  # address text
            message += f"📍 *Location:* {location}\n"
            
        message += f"⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}\n"
        
        if coords or isinstance(location, tuple):
            if isinstance(location, tuple):
                lat, lon = location
            else:
                lat, lon = coords
            message += f"🗺️ *Google Maps:* https://maps.google.com/?q={lat},{lon}\n"
            message += f"🚗 *Waze:* https://waze.com/ul?ll={lat}%2C{lon}&navigate=yes\n"
        
        message += f"\n🔗 *Source:* @sgaccident Community"
        return message
    
    def extract_location_from_message(self, text: str) -> tuple:
        """Extract location/address from @sgaccident message text"""
        if not text:
            return None, None
        
        # Look for coordinate patterns first
        coord_patterns = [
            r'https://maps\.google\.com/\?q=([\d.-]+),([\d.-]+)',
            r'https://www\.google\.com/maps.*@([\d.-]+),([\d.-]+)',
            r'https://goo\.gl/maps/.*?([\d.-]+),([\d.-]+)',
            r'([\d.]+),\s*([\d.]+)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    # Validate Singapore coordinates
                    if 1.0 <= lat <= 1.5 and 103.6 <= lon <= 104.1:
                        return lat, lon
                except ValueError:
                    continue
        
        # If no coordinates, extract address text
        location_patterns = [
            r'accident (?:at|along|near)\s+([^\n.!?]+)',
            r'(?:at|along|near)\s+([^\n.!?]+?)(?:\s+accident|$)',
            r'([A-Z][^\n.!?]*(?:road|rd|ave|avenue|st|street|drive|dr|way|lane|ln)[^\n.!?]*)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 3:  # Basic validation
                    return location, None
        
        return None, None
        lat = accident.get('location', {}).get('y', 0)
        lon = accident.get('location', {}).get('x', 0)
        pub_millis = accident.get('pubMillis', 0)
        return f"{lat}_{lon}_{pub_millis}"
    
    def monitor_and_post(self, check_interval: int = 60):
        print("Starting Enhanced Waze Accident Monitor (Secondary)...")
        print(f"Bot: 8500211695 -> Channel: -1003683261194")
        print(f"Monitoring: Waze API + @sgaccident channel")
        print(f"Checking every {check_interval} seconds")
        
        while True:
            try:
                total_posted = 0
                
                # 1. Process @sgaccident updates first (higher priority)
                sg_posted = self.process_sgaccident_updates()
                if sg_posted > 0:
                    print(f"📱 Posted {sg_posted} accidents from @sgaccident")
                    total_posted += sg_posted
                
                # 2. Process Waze alerts
                alerts = self.get_waze_alerts()
                print(f"📡 Fetched {len(alerts)} Waze alerts")
                
                accidents = self.filter_accidents(alerts)
                print(f"🚗 Found {len(accidents)} Waze accidents")
                
                waze_posted = 0
                for accident in accidents:
                    accident_id = self.get_accident_id(accident)
                    
                    if accident_id not in self.posted_accidents:
                        # Extract and normalize address
                        street = accident.get('street', 'Unknown')
                        normalized_street = self.normalize_address(street)
                        
                        # Check if already posted from @sgaccident
                        if normalized_street in self.posted_addresses:
                            print(f"⚠️ Skipping Waze accident - already posted from @sgaccident: {street}")
                            self.posted_accidents.add(accident_id)
                            continue
                        
                        print(f"🔍 New Waze accident: {street}")
                        
                        message = self.format_accident_message(accident)
                        if self.send_telegram_message(message):
                            print(f"✅ Posted Waze accident: {street}")
                            self.posted_accidents.add(accident_id)
                            self.posted_addresses.add(normalized_street)
                            self.waze_addresses.add(normalized_street)  # Track as Waze source
                            waze_posted += 1
                        else:
                            print(f"❌ Failed to post Waze accident")
                    else:
                        print(f"⚠️ Duplicate Waze accident skipped: {accident.get('street', 'Unknown')}")
                
                total_posted += waze_posted
                if waze_posted > 0:
                    print(f"🚗 Posted {waze_posted} accidents from Waze")
                
                # Clean up old data (keep last 300 items)
                if len(self.posted_accidents) > 300:
                    self.posted_accidents = set(list(self.posted_accidents)[-150:])
                if len(self.posted_addresses) > 300:
                    self.posted_addresses = set(list(self.posted_addresses)[-150:])
                if len(self.waze_addresses) > 300:
                    self.waze_addresses = set(list(self.waze_addresses)[-150:])
                if len(self.processed_messages) > 300:
                    self.processed_messages = set(list(self.processed_messages)[-150:])
                
                print(f"📊 Total posted this cycle: {total_posted} | Tracking: {len(self.posted_addresses)} locations")
                print(f"⏰ Waiting {check_interval} seconds...")
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(30)

def main():
    TELEGRAM_BOT_TOKEN = '8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U'
    TELEGRAM_CHANNEL_ID = '-1003683261194'
    
    monitor = WazeAccidentMonitor(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
    monitor.monitor_and_post(check_interval=60)

if __name__ == "__main__":
    main()