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
import sys
import pytz

# Ensure unbuffered output for systemd logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Singapore timezone
SINGAPORE_TZ = pytz.timezone('Asia/Singapore')

class WazeAccidentMonitor:
    def __init__(self, telegram_bot_token: str, telegram_channel_id: str, 
                 coordinate_precision: int = 3, time_window_hours: int = 1, 
                 max_stored_accidents: int = 5000, max_stored_coordinates: int = 5000):
        """
        Initialize the Waze Accident Monitor - Secondary Channel Version
        
        Args:
            telegram_bot_token: Your Telegram bot token from @BotFather
            telegram_channel_id: Your Telegram channel ID (e.g., @yourchannel or -100xxxxxxxxx)
            coordinate_precision: Decimal places for coordinate matching (3 = ~111m, 4 = ~11m)
            time_window_hours: Hours to group accidents (1 = same hour, 24 = same day)
            max_stored_accidents: Maximum accident IDs to keep in memory
            max_stored_coordinates: Maximum coordinate IDs to keep in memory
        """
        self.telegram_bot_token = telegram_bot_token
        self.telegram_channel_id = telegram_channel_id
        self.telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}"
        
        # Configurable duplicate detection parameters
        self.coordinate_precision = coordinate_precision
        self.time_window_hours = time_window_hours
        self.max_stored_accidents = max_stored_accidents
        self.max_stored_coordinates = max_stored_coordinates
        
        self.posted_accidents: Set[str] = set()
        self.posted_coordinates: Set[str] = set()  # Track posted coordinates to prevent duplicates
        self.processed_messages: Set[str] = set()  # Track processed messages from sgaccident
        self.last_update_id = None  # Track last processed update ID
        
        # File paths for persistent storage (secondary channel specific)
        self.accidents_file = "posted_accidents_secondary.txt"
        self.coordinates_file = "posted_coordinates_secondary.txt"
        
        # Load existing data
        self.load_posted_data()
        
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
            utc_time = datetime.fromtimestamp(pub_millis / 1000, tz=pytz.UTC)
            singapore_time = utc_time.astimezone(SINGAPORE_TZ)
            report_time = singapore_time.strftime('%Y-%m-%d %H:%M:%S SGT')
        else:
            report_time = 'Unknown time'
        
        # Format message
        emoji = "🚨"
        if 'MAJOR' in str(subtype).upper() or 'MAJOR' in str(accident_type).upper():
            emoji = "🚨🚨🚨"
        elif 'MINOR' in str(subtype).upper() or 'MINOR' in str(accident_type).upper():
            emoji = "⚠️"
            
        # Format location in @sgaccident style
        if street and city and city != 'Singapore':
            location_text = f"Accident on {street}, {city}"
        elif street:
            location_text = f"Accident on {street}"
        elif city:
            location_text = f"Accident in {city}"
        else:
            location_text = "Accident at unknown location"
            
        message = f"{location_text}\n"
        message += f"🕐 *Reported:* {report_time}\n"
        
        if subtype:
            message += f"📊 *Type:* {subtype.replace('_', ' ').title()}\n"
        
        message += f"👤 *Reported by:* {reported_by}\n"
        message += f"📈 *Confidence:* {confidence}/10\n"
        message += f"✅ *Reliability:* {reliability}/10\n"
        
        if lat and lon:
            google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
            message += f"\n🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_link})\n"
            message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_link})\n"
        
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
    
    def addresses_similar(self, addr1: str, addr2: str) -> bool:
        """
        Check if two addresses are similar enough to be considered duplicates
        
        Args:
            addr1: First address
            addr2: Second address
            
        Returns:
            True if addresses are similar
        """
        if not addr1 or not addr2:
            return False
            
        # Normalize both addresses
        norm1 = self.normalize_address(addr1).lower()
        norm2 = self.normalize_address(addr2).lower()
        
        # Exact match
        if norm1 == norm2:
            return True
            
        # Check if one contains the other (for different detail levels)
        if norm1 in norm2 or norm2 in norm1:
            return True
            
        # Split into words and check overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # If more than 70% of words overlap, consider similar
        if words1 and words2:
            overlap = len(words1.intersection(words2))
            min_words = min(len(words1), len(words2))
            if overlap / min_words > 0.7:
                return True
                
        return False
        
    def normalize_address(self, address: str) -> str:
        """
        Normalize address string for duplicate detection
        
        Args:
            address: Raw address string
            
        Returns:
            Normalized address string
        """
        if not address:
            return ""
            
        # Convert to lowercase and strip whitespace
        normalized = address.lower().strip()
        
        # Remove common prefixes and suffixes
        prefixes_to_remove = ['accident at', 'accident along', 'at', 'along', 'near', 'opposite', 'opp']
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix + ' '):
                normalized = normalized[len(prefix):].strip()
        
        # Standardize road abbreviations
        road_replacements = {
            ' rd': ' road',
            ' st': ' street', 
            ' ave': ' avenue',
            ' blvd': ' boulevard',
            ' hwy': ' highway',
            ' expy': ' expressway',
            ' tpk': ' turnpike',
            ' cres': ' crescent',
            ' gdns': ' gardens',
            ' pk': ' park',
            ' sq': ' square'
        }
        
        for abbrev, full in road_replacements.items():
            normalized = normalized.replace(abbrev, full)
            
        # Remove extra spaces and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def load_posted_data(self):
        """Load previously posted accidents and coordinates from files"""
        try:
            if os.path.exists(self.accidents_file):
                with open(self.accidents_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.posted_accidents.add(line.strip())
                print(f"Loaded {len(self.posted_accidents)} previously posted accidents")
        except Exception as e:
            print(f"Warning: Could not load posted accidents: {e}")
            
        try:
            if os.path.exists(self.coordinates_file):
                with open(self.coordinates_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.posted_coordinates.add(line.strip())
                print(f"Loaded {len(self.posted_coordinates)} previously posted coordinates")
        except Exception as e:
            print(f"Warning: Could not load posted coordinates: {e}")
    
    def save_posted_data(self, accident_id=None, coordinate_id=None):
        """Save posted accidents and coordinates to files"""
        try:
            if accident_id:
                with open(self.accidents_file, 'a') as f:
                    f.write(f"{accident_id}\n")
        except Exception as e:
            print(f"Warning: Could not save accident ID: {e}")
            
        try:
            if coordinate_id:
                with open(self.coordinates_file, 'a') as f:
                    f.write(f"{coordinate_id}\n")
        except Exception as e:
            print(f"Warning: Could not save coordinate ID: {e}")
    
    def get_coordinate_id_from_text(self, text: str) -> str:
        """
        Extract coordinate and time-based ID from message text for duplicate detection
        
        Args:
            text: Message text
            
        Returns:
            Coordinate and time-based ID string or text-based fallback with configurable precision
        """
        lat, lon = self.extract_coordinates(text)
        
        # Use current time for grouping since message timestamps may not be accident time
        current_time = datetime.now(SINGAPORE_TZ)
        
        # Generate time window based on configuration
        if self.time_window_hours == 1:
            time_window = current_time.strftime('%Y%m%d_%H')  # Hour precision
        elif self.time_window_hours == 24:
            time_window = current_time.strftime('%Y%m%d')     # Day precision
        else:
            # Custom hour grouping
            hour_group = (current_time.hour // self.time_window_hours) * self.time_window_hours
            time_window = current_time.strftime(f'%Y%m%d_{hour_group:02d}')
        
        if lat and lon:
            # Use configurable coordinate precision
            return f"coord_{lat:.{self.coordinate_precision}f}_{lon:.{self.coordinate_precision}f}_{time_window}"
        else:
            # Fallback to text-based if no coordinates
            address = self.extract_address_from_text(text)
            return f"text_{self.normalize_address(address)}_{time_window}"

    def get_coordinate_id(self, accident: Dict) -> str:
        """
        Extract coordinate and time-based ID from Waze accident data for duplicate detection
        
        Args:
            accident: Waze accident dictionary
            
        Returns:
            Coordinate and time-based ID string (rounded to ~50m precision and 1-hour time window)
        """
        location = accident.get('location', {})
        lat = location.get('y', 0)
        lon = location.get('x', 0)
        pub_millis = accident.get('pubMillis', 0)
        
        if lat and lon and pub_millis:
            # Round coordinates to 3 decimal places (~111m precision) to catch nearby duplicates
            # Round timestamp to hour to group accidents within same time period
            utc_time = datetime.fromtimestamp(pub_millis / 1000, tz=pytz.UTC)
            singapore_time = utc_time.astimezone(SINGAPORE_TZ)
            time_hour = singapore_time.strftime('%Y%m%d_%H')  # Group by date and hour
            return f"coord_{lat:.3f}_{lon:.3f}_{time_hour}"
        elif lat and lon:
            # Fallback without timestamp
            from datetime import datetime
            current_time = datetime.now(SINGAPORE_TZ)
            time_hour = current_time.strftime('%Y%m%d_%H')
            return f"coord_{lat:.3f}_{lon:.3f}_{time_hour}"
        else:
            # Fallback to text-based if no coordinates
            street = accident.get('street', '')
            city = accident.get('city', '')
            if street and city:
                return f"text_{self.normalize_address(f'{street}, {city}')}"
            elif street:
                return f"text_{self.normalize_address(street)}"
            else:
                return f"text_unknown_location"
        
    def extract_address_from_text(self, text: str) -> str:
        """
        Extract and normalize address from message text
        
        Args:
            text: Message text
            
        Returns:
            Normalized address string
        """
        if not text:
            return ""
            
        # Look for common Singapore location patterns
        location_patterns = [
            r'accident (?:at|along|near) ([^\n]+)',
            r'(?:at|along|near) ([^,\n]+)',
            r'([A-Z][^\n]*(?:Road|Street|Avenue|Drive|Lane|Way|Circle|Crescent|Gardens|Park|Square|Boulevard|Highway|Expressway)[^\n]*)',
            r'([A-Z][^\n]*(?:Rd|St|Ave|Dr|Ln|Cir|Cres|Gdns|Pk|Sq|Blvd|Hwy|Expy)[^\n]*)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                address = match.group(1).strip()
                if len(address) > 3:  # Ensure it's not just a short word
                    return self.normalize_address(address)
        
        # Fallback: try to extract coordinates and use them as address
        lat, lon = self.extract_coordinates(text)
        if lat and lon:
            return self.normalize_address(f"coordinates_{lat:.4f}_{lon:.4f}")
            
        # Last resort: use first meaningful part of text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line) > 10:
                return self.normalize_address(first_line[:100])  # Limit length
                
        return self.normalize_address(text[:50])  # Very last resort
    
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
        singapore_now = datetime.now(SINGAPORE_TZ)
        timestamp = singapore_now.strftime('%Y-%m-%d %H:%M:%S SGT')
        
        message = f" *Reported:* {timestamp}\n\n"
        
        # Add original message content
        message += f"📝 *Details:*\n{original_message}\n\n"
        
        # Add map links if coordinates are available
        if lat and lon:
            google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
            message += f"🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_link})\n"
            message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_link})\n"
        
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
                
                # Check if it's from sgaccident channel (ID: -1001486947378 or username: sgaccident)
                chat = post.get('chat', {})
                if chat.get('username') == 'sgaccident' or str(chat.get('id')) == '-1001486947378':
                    message_id = f"sgaccident_{post.get('message_id')}"
                    
                    # Skip if already processed
                    if message_id in self.processed_messages:
                        continue
                    
                    message_text = post.get('text', '')
                    if message_text:
                        # Extract coordinate-based ID for duplicate detection
                        coordinate_id = self.get_coordinate_id_from_text(message_text)
                        
                        # Skip if same coordinates already posted
                        if coordinate_id and coordinate_id in self.posted_coordinates:
                            print(f"⚠️ Skipping duplicate coordinates from @sgaccident: {coordinate_id}")
                            continue
                        
                        # Extract coordinates for map links
                        lat, lon = self.extract_coordinates(message_text)
                        
                        # Format and send message
                        formatted_message = self.format_sgaccident_message(message_text, lat, lon)
                        
                        if self.send_telegram_message(formatted_message):
                            print(f"✓ Reposted from @sgaccident: {message_text[:50]}...")
                            self.processed_messages.add(message_id)
                            if coordinate_id:
                                self.posted_coordinates.add(coordinate_id)
                                self.save_posted_data(coordinate_id=coordinate_id)
                            processed_count += 1
                        else:
                            print(f"✗ Failed to repost from @sgaccident")
            
            # Also check for forwarded messages that might be from sgaccident
            elif 'message' in update:
                message = update['message']
                forward_from_chat = message.get('forward_from_chat', {})
                
                if forward_from_chat.get('username') == 'sgaccident' or str(forward_from_chat.get('id')) == '-1001486947378':
                    message_id = f"forward_sgaccident_{message.get('message_id')}"
                    
                    if message_id not in self.processed_messages:
                        message_text = message.get('text', '')
                        if message_text:
                            # Extract coordinate-based ID for duplicate detection
                            coordinate_id = self.get_coordinate_id_from_text(message_text)
                            
                            # Skip if same coordinates already posted
                            if coordinate_id and coordinate_id in self.posted_coordinates:
                                print(f"⚠️ Skipping duplicate coordinates from forwarded @sgaccident: {coordinate_id}")
                                continue
                                
                            lat, lon = self.extract_coordinates(message_text)
                            formatted_message = self.format_sgaccident_message(message_text, lat, lon)
                            
                            if self.send_telegram_message(formatted_message):
                                print(f"✓ Reposted forwarded from @sgaccident: {message_text[:50]}...")
                                self.processed_messages.add(message_id)
                                if coordinate_id:
                                    self.posted_coordinates.add(coordinate_id)
                                    self.save_posted_data(coordinate_id=coordinate_id)
                                processed_count += 1
        
        # Clean up old processed messages and coordinates (keep only last 1000)
        if len(self.processed_messages) > 1000:
            self.processed_messages = set(list(self.processed_messages)[-500:])
            
        if len(self.posted_coordinates) > 2000:  # Keep more coordinates for better duplicate detection
            self.posted_coordinates = set(list(self.posted_coordinates)[-1000:])
            
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
    
    def monitor_and_post(self, check_interval: int = 60):
        """
        Continuously monitor Waze for accidents and post to Telegram
        Also monitors @sgaccident channel for updates
        
        Args:
            check_interval: Seconds between checks (default: 60 = 1 minute)
        """
        print("Starting Enhanced Accident Monitor - Secondary Channel...")
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
                        # Check for duplicate coordinates
                        coordinate_id = self.get_coordinate_id(accident)
                        
                        if coordinate_id and coordinate_id in self.posted_coordinates:
                            print(f"⚠️ Skipping duplicate Waze accident at: {coordinate_id}")
                            continue
                        
                        message = self.format_accident_message(accident)
                        if self.send_telegram_message(message):
                            print(f"✓ Posted Waze accident: {accident.get('street', 'Unknown')}")
                            self.posted_accidents.add(accident_id)
                            self.save_posted_data(accident_id=accident_id, coordinate_id=coordinate_id)
                            if coordinate_id:
                                self.posted_coordinates.add(coordinate_id)
                            waze_posted += 1
                        else:
                            print(f"✗ Failed to post Waze accident: {accident.get('street', 'Unknown')}")
                
                # Clean up old accident IDs and coordinates using configurable limits
                if len(self.posted_accidents) > self.max_stored_accidents:
                    self.posted_accidents = set(list(self.posted_accidents)[-(self.max_stored_accidents//2):])
                
                if len(self.posted_coordinates) > self.max_stored_coordinates:
                    self.posted_coordinates = set(list(self.posted_coordinates)[-(self.max_stored_coordinates//2):])
                
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
    Main function to run the monitor with configurable duplicate detection
    """
    # Get credentials from environment variables or set them here
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '-1003683261194')
    
    # Configurable duplicate detection parameters
    # coordinate_precision: 3 = ~111m radius, 4 = ~11m radius, 2 = ~1100m radius
    # time_window_hours: 1 = hourly grouping, 4 = 4-hour blocks, 24 = daily grouping
    COORDINATE_PRECISION = int(os.getenv('COORDINATE_PRECISION', '3'))
    TIME_WINDOW_HOURS = int(os.getenv('TIME_WINDOW_HOURS', '1'))
    MAX_STORED_ACCIDENTS = int(os.getenv('MAX_STORED_ACCIDENTS', '5000'))
    MAX_STORED_COORDINATES = int(os.getenv('MAX_STORED_COORDINATES', '5000'))
    
    # Create monitor with configurable parameters
    monitor = WazeAccidentMonitor(
        TELEGRAM_BOT_TOKEN, 
        TELEGRAM_CHANNEL_ID,
        coordinate_precision=COORDINATE_PRECISION,
        time_window_hours=TIME_WINDOW_HOURS,
        max_stored_accidents=MAX_STORED_ACCIDENTS,
        max_stored_coordinates=MAX_STORED_COORDINATES
    )
    
    print(f"Duplicate Detection Config:")
    print(f"  Coordinate Precision: {COORDINATE_PRECISION} decimal places (~{111/(10**COORDINATE_PRECISION):.0f}m radius)")
    print(f"  Time Window: {TIME_WINDOW_HOURS} hour(s)")
    print(f"  Max Stored: {MAX_STORED_ACCIDENTS} accidents, {MAX_STORED_COORDINATES} coordinates")
    
    # Check every 1 minute (60 seconds)
    monitor.monitor_and_post(check_interval=60)


if __name__ == "__main__":
    main()
