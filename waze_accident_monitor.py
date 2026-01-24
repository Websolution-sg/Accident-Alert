"""
Waze Accident Monitor - Extracts accident occurrences and posts to Telegram
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
        """
        Initialize the Waze Accident Monitor
        
        Args:
            telegram_bot_token: Your Telegram bot token from @BotFather
            telegram_channel_id: Your Telegram channel ID (e.g., @yourchannel or -100xxxxxxxxx)
        """
        self.telegram_bot_token = telegram_bot_token
        self.telegram_channel_id = telegram_channel_id
        self.telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}"
        self.posted_accidents: Set[str] = set()
        self.processed_messages: Set[str] = set()  # Track processed messages from sgaccident
        self.last_update_id = None  # Track last processed update ID
        
        # Singapore bounding box
        self.bbox = {
            'bottom': 1.1304753,
            'left': 103.6055424,
            'right': 104.0945619,
            'top': 1.4764671
        }
        
    def get_waze_alerts(self) -> List[Dict]:
        """
        Fetch alerts from Waze API for Singapore
        
        Returns:
            List of alert dictionaries
        """
        # Waze Live Map API endpoint
        url = "https://www.waze.com/live-map/api/georss"
        
        params = {
            'bottom': self.bbox['bottom'],
            'left': self.bbox['left'],
            'right': self.bbox['right'],
            'top': self.bbox['top'],
            'env': 'row',
            'types': 'alerts,traffic'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('alerts', [])
        except requests.RequestException as e:
            print(f"Error fetching Waze data: {e}")
            return []
    
    def filter_accidents(self, alerts: List[Dict]) -> List[Dict]:
        """
        Filter alerts to get only accidents in Singapore
        
        Args:
            alerts: List of all alerts
            
        Returns:
            List of accident alerts in Singapore only
        """
        accident_types = ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR']
        accidents = [
            alert for alert in alerts 
            if (alert.get('type', '').upper() in accident_types or 
                alert.get('subtype', '').upper() in accident_types) and
               (alert.get('country', '').upper() in ['SG', 'SN'] or 
                'SINGAPORE' in alert.get('city', '').upper() or
                alert.get('city', '') in ['Outram', 'Kallang', 'Geylang', 'Bukit Timah', 'Sentosa', 'Tampines', 'Woodlands', 'Jurong', 'Bedok', 'Punggol', 'Sengkang', 'Yishun', 'Ang Mo Kio', 'Bishan', 'Toa Payoh', 'Queenstown', 'Clementi', 'Pasir Ris', 'Sembawang', 'Marine Parade'])
        ]
        return accidents
    
    def format_accident_message(self, accident: Dict) -> str:
        """
        Format accident information for Telegram message
        
        Args:
            accident: Accident alert dictionary
            
        Returns:
            Formatted message string
        """
        # Extract information
        accident_type = accident.get('type', 'ACCIDENT')
        subtype = accident.get('subtype', '')
        street = accident.get('street', 'Unknown location')
        city = accident.get('city', 'Singapore')
        country = accident.get('country', 'SG')
        reported_by = accident.get('reportBy', 'Waze user')
        confidence = accident.get('confidence', 0)
        reliability = accident.get('reliability', 0)
        
        # Get coordinates
        location = accident.get('location', {})
        lat = location.get('y', 0)
        lon = location.get('x', 0)
        
        # Get timestamp
        pub_millis = accident.get('pubMillis', 0)
        if pub_millis:
            report_time = datetime.fromtimestamp(pub_millis / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            report_time = 'Unknown time'
        
        # Format message
        emoji = "🚨"
        if 'MAJOR' in str(subtype).upper() or 'MAJOR' in str(accident_type).upper():
            emoji = "🚨🚨🚨"
        elif 'MINOR' in str(subtype).upper() or 'MINOR' in str(accident_type).upper():
            emoji = "⚠️"
            
        message = f"{emoji} *ACCIDENT ALERT* {emoji}\n\n"
        message += f"📍 *Location:* {street}, {city}\n"
        message += f"🕐 *Reported:* {report_time}\n"
        
        if subtype:
            message += f"📊 *Type:* {subtype.replace('_', ' ').title()}\n"
        
        message += f"👤 *Reported by:* {reported_by}\n"
        message += f"📈 *Confidence:* {confidence}/10\n"
        message += f"✅ *Reliability:* {reliability}/10\n"
        
        if lat and lon:
            google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
            message += f"\n🗺️ [View on Google Maps]({google_maps_link})\n"
            message += f"🚗 [Open in Waze]({waze_link})\n"
        
        return message
    
    def send_telegram_message(self, message: str) -> bool:
        """
        Send message to Telegram channel
        
        Args:
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.telegram_api_url}/sendMessage"
        
        payload = {
            'chat_id': self.telegram_channel_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def get_channel_updates(self) -> List[Dict]:
        """
        Get updates from Telegram, including messages from channels
        
        Returns:
            List of update dictionaries
        """
        url = f"{self.telegram_api_url}/getUpdates"
        
        params = {
            'timeout': 10,
            'limit': 100
        }
        
        if self.last_update_id:
            params['offset'] = self.last_update_id + 1
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                updates = data.get('result', [])
                if updates:
                    self.last_update_id = updates[-1]['update_id']
                return updates
            else:
                print(f"Telegram API error: {data.get('description', 'Unknown error')}")
                return []
                
        except requests.RequestException as e:
            print(f"Error fetching updates: {e}")
            return []
    
    def extract_coordinates(self, text: str) -> tuple:
        """
        Extract coordinates from text using various patterns
        
        Args:
            text: Message text to search for coordinates
            
        Returns:
            Tuple of (latitude, longitude) or (None, None) if not found
        """
        if not text:
            return None, None
            
        # Pattern 1: Decimal degrees (1.234567, 103.123456)
        decimal_pattern = r'[-+]?([1-8]?\d(?:\.\d+)?|90(?:\.0+)?),\s*[-+]?(180(?:\.0+)?|1[0-7]\d(?:\.\d+)?|\d{1,2}(?:\.\d+)?)'
        
        # Pattern 2: Google Maps links
        gmaps_pattern = r'maps\.google\.com[^\s]*[@,](-?\d+\.\d+),(-?\d+\.\d+)'
        
        # Pattern 3: Waze links
        waze_pattern = r'waze\.com[^\s]*ll=(-?\d+\.\d+),(-?\d+\.\d+)'
        
        # Pattern 4: Location pins or coordinates in various formats
        coord_pattern = r'(?:lat|latitude)[:\s]*(-?\d+\.\d+)[\s,]+(?:lon|lng|longitude)[:\s]*(-?\d+\.\d+)'
        
        # Try each pattern
        patterns = [
            (decimal_pattern, lambda m: (float(m.group().split(',')[0]), float(m.group().split(',')[1]))),
            (gmaps_pattern, lambda m: (float(m.group(1)), float(m.group(2)))),
            (waze_pattern, lambda m: (float(m.group(1)), float(m.group(2)))),
            (coord_pattern, lambda m: (float(m.group(1)), float(m.group(2))))
        ]
        
        for pattern, extractor in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    lat, lon = extractor(match)
                    # Validate Singapore coordinates roughly
                    if 1.0 <= lat <= 1.5 and 103.6 <= lon <= 104.1:
                        return lat, lon
                except (ValueError, IndexError):
                    continue
                    
        return None, None
    
    def format_sgaccident_message(self, original_message: str, lat: float = None, lon: float = None) -> str:
        """
        Format message from sgaccident channel with Waze links
        
        Args:
            original_message: Original message text
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Formatted message string
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"🚨 *ACCIDENT ALERT* (via @sgaccident)\n\n"
        message += f"📅 *Reported:* {timestamp}\n\n"
        
        # Add original message content
        message += f"📝 *Details:*\n{original_message}\n\n"
        
        # Add map links if coordinates are available
        if lat and lon:
            google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
            message += f"🗺️ [View on Google Maps]({google_maps_link})\n"
            message += f"🚗 [Open in Waze]({waze_link})\n"
        
        message += f"\n📡 *Source:* @sgaccident"
        
        return message
    
    def process_sgaccident_updates(self) -> int:
        """
        Process updates from sgaccident channel and repost to own channel
        
        Returns:
            Number of new messages processed
        """
        updates = self.get_channel_updates()
        processed_count = 0
        
        for update in updates:
            # Look for channel posts
            if 'channel_post' in update:
                post = update['channel_post']
                
                # Check if it's from sgaccident channel (username: sgaccident)
                chat = post.get('chat', {})
                if chat.get('username') == 'sgaccident':
                    message_id = f"sgaccident_{post.get('message_id')}"
                    
                    # Skip if already processed
                    if message_id in self.processed_messages:
                        continue
                    
                    message_text = post.get('text', '')
                    if message_text:
                        # Extract coordinates
                        lat, lon = self.extract_coordinates(message_text)
                        
                        # Format and send message
                        formatted_message = self.format_sgaccident_message(message_text, lat, lon)
                        
                        if self.send_telegram_message(formatted_message):
                            print(f"✓ Reposted from @sgaccident: {message_text[:50]}...")
                            self.processed_messages.add(message_id)
                            processed_count += 1
                        else:
                            print(f"✗ Failed to repost from @sgaccident")
            
            # Also check for forwarded messages that might be from sgaccident
            elif 'message' in update:
                message = update['message']
                forward_from_chat = message.get('forward_from_chat', {})
                
                if forward_from_chat.get('username') == 'sgaccident':
                    message_id = f"forward_sgaccident_{message.get('message_id')}"
                    
                    if message_id not in self.processed_messages:
                        message_text = message.get('text', '')
                        if message_text:
                            lat, lon = self.extract_coordinates(message_text)
                            formatted_message = self.format_sgaccident_message(message_text, lat, lon)
                            
                            if self.send_telegram_message(formatted_message):
                                print(f"✓ Reposted forwarded from @sgaccident: {message_text[:50]}...")
                                self.processed_messages.add(message_id)
                                processed_count += 1
        
        # Clean up old processed messages (keep only last 1000)
        if len(self.processed_messages) > 1000:
            self.processed_messages = set(list(self.processed_messages)[-500:])
            
        return processed_count
    
    def get_accident_id(self, accident: Dict) -> str:
        """
        Generate unique ID for an accident
        
        Args:
            accident: Accident dictionary
            
        Returns:
            Unique ID string
        """
        uuid = accident.get('uuid', '')
        if uuid:
            return uuid
        
        # Fallback: use location and time
        location = accident.get('location', {})
        lat = location.get('y', 0)
        lon = location.get('x', 0)
        pub_millis = accident.get('pubMillis', 0)
        return f"{lat}_{lon}_{pub_millis}"
    
    def monitor_and_post(self, check_interval: int = 300):
        """
        Continuously monitor Waze for accidents and post to Telegram
        Also monitors @sgaccident channel for updates
        
        Args:
            check_interval: Seconds between checks (default: 300 = 5 minutes)
        """
        print("Starting Enhanced Accident Monitor...")
        print(f"Checking every {check_interval} seconds")
        print(f"Posting to Telegram channel: {self.telegram_channel_id}")
        print("Also monitoring @sgaccident channel for updates")
        
        while True:
            try:
                # 1. Process updates from @sgaccident channel
                sg_processed = self.process_sgaccident_updates()
                if sg_processed > 0:
                    print(f"Processed {sg_processed} updates from @sgaccident")
                
                # 2. Fetch Waze alerts
                alerts = self.get_waze_alerts()
                print(f"Fetched {len(alerts)} total alerts")
                
                # Filter for accidents
                accidents = self.filter_accidents(alerts)
                print(f"Found {len(accidents)} accidents")
                
                # Post new accidents
                waze_posted = 0
                for accident in accidents:
                    accident_id = self.get_accident_id(accident)
                    
                    if accident_id not in self.posted_accidents:
                        message = self.format_accident_message(accident)
                        if self.send_telegram_message(message):
                            print(f"✓ Posted Waze accident: {accident.get('street', 'Unknown')}")
                            self.posted_accidents.add(accident_id)
                            waze_posted += 1
                        else:
                            print(f"✗ Failed to post Waze accident: {accident.get('street', 'Unknown')}")
                
                # Clean up old accident IDs (keep only last 1000)
                if len(self.posted_accidents) > 1000:
                    self.posted_accidents = set(list(self.posted_accidents)[-500:])
                
                # Summary
                total_posted = sg_processed + waze_posted
                if total_posted > 0:
                    print(f"Total alerts posted this cycle: {total_posted}")
                
                print(f"Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """
    Main function to run the monitor
    """
    # Get credentials from environment variables or set them here
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '-1003329968129')
    
    # Bot token and channel ID are already configured
    
    # Create monitor and start
    monitor = WazeAccidentMonitor(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
    
    # Check every 1 minute (60 seconds)
    monitor.monitor_and_post(check_interval=60)


if __name__ == "__main__":
    main()
