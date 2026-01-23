"""
Waze Accident Monitor - Extracts accident occurrences and posts to Telegram
"""
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Set
import os

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
        Filter alerts to get only accidents
        
        Args:
            alerts: List of all alerts
            
        Returns:
            List of accident alerts
        """
        accident_types = ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR']
        accidents = [
            alert for alert in alerts 
            if alert.get('type', '').upper() in accident_types or 
            alert.get('subtype', '').upper() in accident_types
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
        
        Args:
            check_interval: Seconds between checks (default: 300 = 5 minutes)
        """
        print("Starting Waze Accident Monitor...")
        print(f"Checking every {check_interval} seconds")
        print(f"Posting to Telegram channel: {self.telegram_channel_id}")
        
        while True:
            try:
                # Fetch alerts
                alerts = self.get_waze_alerts()
                print(f"Fetched {len(alerts)} total alerts")
                
                # Filter for accidents
                accidents = self.filter_accidents(alerts)
                print(f"Found {len(accidents)} accidents")
                
                # Post new accidents
                for accident in accidents:
                    accident_id = self.get_accident_id(accident)
                    
                    if accident_id not in self.posted_accidents:
                        message = self.format_accident_message(accident)
                        if self.send_telegram_message(message):
                            print(f"✓ Posted accident: {accident.get('street', 'Unknown')}")
                            self.posted_accidents.add(accident_id)
                        else:
                            print(f"✗ Failed to post accident: {accident.get('street', 'Unknown')}")
                
                # Clean up old accident IDs (keep only last 1000)
                if len(self.posted_accidents) > 1000:
                    self.posted_accidents = set(list(self.posted_accidents)[-500:])
                
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
    
    # Check every 5 minutes (300 seconds)
    monitor.monitor_and_post(check_interval=300)


if __name__ == "__main__":
    main()
