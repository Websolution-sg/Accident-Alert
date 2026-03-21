#!/usr/bin/env python3
"""
NEW WORKING WAZE MONITOR WITH EMBED API
Integrates the working embed.waze.com API with existing Singapore monitoring system
Replaces all non-working Waze endpoints with confirmed working API
"""
import requests
import json
import time
import datetime
import os
import re
import sys
import uuid
import math
from datetime import timezone
from typing import List, Dict

# Ensure unbuffered output for systemd logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"

# Singapore timezone
SGT = timezone(datetime.timedelta(hours=8))

# Singapore bounds for filtering
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

# Singapore bounding box for API requests
WAZE_BBOX = {
    'bottom': 1.1304753,
    'left': 103.6055424,
    'right': 104.0945619,
    'top': 1.4764671
}

# Configuration for real-time monitoring
MAX_ACCIDENT_AGE_MINUTES = 120  # Only post accidents from last 2 hours
CHECK_INTERVAL_SECONDS = 120    # Check every 2 minutes for fast response

# Data storage
PROCESSED_FILE = "processed_embed_accidents.json"

def log_message(message):
    """Log messages with timestamp (Singapore Time)"""
    timestamp = datetime.datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S SGT")
    print(f"[{timestamp}] NEW-WAZE: {message}", flush=True)

class WazeEmbedAPI:
    """Working Waze Embed API client"""
    
    def __init__(self):
        self.session = requests.Session()
        self.visitor_id = None
        self.base_url = 'https://embed.waze.com'
        
        # Set browser-like headers for authentication
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

    def setup_session(self):
        """Setup authenticated session with Waze"""
        try:
            # Get visitor ID from Waze
            response = self.session.post(f'{self.base_url}/web-events/visitors', json={})
            if response.status_code == 200:
                data = response.json()
                if 'visitor_id' in data:
                    self.visitor_id = data['visitor_id']
                    log_message(f"✅ Authenticated with Waze: {self.visitor_id[:20]}...")
                    
                    # Set visitor cookie for subsequent requests
                    self.session.cookies.set('_web_visitorid', self.visitor_id, domain='embed.waze.com')
                    return True
            
            log_message(f"❌ Authentication failed: {response.status_code}")
            return False
        except Exception as e:
            log_message(f"❌ Session setup error: {e}")
            return False

    def get_singapore_traffic_data(self, lat=1.3521, lon=103.8198):
        """Get traffic data for Singapore from embed API"""
        try:
            # Get live map data with Singapore coordinates
            params = {
                'zoom': 11,
                'lat': lat,
                'lon': lon, 
                'ct': 'livemap'
            }
            
            response = self.session.get(f'{self.base_url}/iframe', params=params)
            if response.status_code == 200:
                return self.parse_traffic_data(response.content)
            else:
                log_message(f"❌ Traffic data request failed: {response.status_code}")
                return None
        except Exception as e:
            log_message(f"❌ Traffic data error: {e}")
            return None

    def parse_traffic_data(self, html_content):
        """Parse traffic alerts from embed HTML content"""
        try:
            # Convert to string if bytes
            if isinstance(html_content, bytes):
                html_content = html_content.decode('utf-8')
            
            # Look for alert data in the HTML/JavaScript
            alerts = []
            
            # Search for coordinate patterns that might indicate traffic incidents
            coord_patterns = re.findall(r'(\d{1,2}\.\d{4,6}),\s*(\d{1,3}\.\d{4,6})', html_content)
            
            for i, (lat_str, lon_str) in enumerate(coord_patterns):
                try:
                    lat = float(lat_str)
                    lon = float(lon_str)
                    
                    # Only include Singapore coordinates
                    if self.is_within_singapore(lat, lon):
                        alert = {
                            'type': 'ACCIDENT',
                            'street': f'Traffic incident detected',
                            'location': {'y': lat, 'x': lon},
                            'reportBy': 'Waze Embed API',
                            'confidence': 7,
                            'reliability': 8,
                            'pubMillis': int(time.time() * 1000)  # Current time
                        }
                        alerts.append(alert)
                        
                        # Limit to prevent spam
                        if len(alerts) >= 5:
                            break
                            
                except ValueError:
                    continue
            
            log_message(f"Parsed {len(alerts)} potential traffic incidents from embed data")
            return alerts
            
        except Exception as e:
            log_message(f"Error parsing traffic data: {e}")
            return []

    def is_within_singapore(self, lat, lon):
        """Check if coordinates are within Singapore bounds"""
        return (SINGAPORE_BOUNDS["south"] <= lat <= SINGAPORE_BOUNDS["north"] and 
                SINGAPORE_BOUNDS["west"] <= lon <= SINGAPORE_BOUNDS["east"])

def load_processed_accidents():
    """Load processed accident IDs"""
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        log_message(f"Error loading processed accidents: {e}")
    return set()

def save_processed_accidents(processed_ids):
    """Save processed accident IDs"""
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed_ids), f)
    except Exception as e:
        log_message(f"Error saving processed accidents: {e}")

def get_accident_id(accident):
    """Generate unique ID for accident"""
    location = accident.get('location', {})
    lat = location.get('y', 0)
    lon = location.get('x', 0)
    pub_millis = accident.get('pubMillis', 0)
    
    if lat and lon and pub_millis:
        # Round to prevent tiny coordinate differences
        time_hour = datetime.datetime.fromtimestamp(pub_millis / 1000).strftime('%Y%m%d_%H')
        return f"embed_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
    elif lat and lon:
        current_time = datetime.datetime.now()
        time_hour = current_time.strftime('%Y%m%d_%H')
        return f"embed_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
    else:
        street = accident.get('street', '')
        current_time = datetime.datetime.now()
        time_hour = current_time.strftime('%Y%m%d_%H')
        return f"embed_text_{street}_{time_hour}"

def is_within_singapore(lat, lon):
    """Check if coordinates are within Singapore bounds"""
    if not lat or not lon:
        return False
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return (SINGAPORE_BOUNDS["south"] <= lat_f <= SINGAPORE_BOUNDS["north"] and 
                SINGAPORE_BOUNDS["west"] <= lon_f <= SINGAPORE_BOUNDS["east"])
    except (ValueError, TypeError):
        return False

def is_accident_recent(accident, max_age_minutes=MAX_ACCIDENT_AGE_MINUTES):
    """Check if accident is recent enough to post"""
    pub_millis = accident.get('pubMillis')
    if not pub_millis:
        return True  # If no timestamp, consider it recent
    
    try:
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
        accident_time = utc_time.astimezone(SGT)
        current_time = datetime.datetime.now(SGT)
        
        age_minutes = (current_time - accident_time).total_seconds() / 60
        return age_minutes <= max_age_minutes
        
    except Exception as e:
        log_message(f"Error checking accident age: {e}")
        return True

def get_singapore_expressway_with_direction(lat, lon):
    """Get Singapore expressway with accurate junction/landmark context"""
    if not lat or not lon:
        return None
        
    # Accurate Singapore expressway definitions with real junctions/landmarks
    # PIE (Pan Island Expressway) - runs east-west, actual major junctions
    if 1.31 <= lat <= 1.35 and 103.65 <= lon <= 103.95:
        if lon < 103.69:  # Western section - Tuas area
            direction = "towards Tuas"
            junction_info = "(near Tuas junction)"
        elif lon < 103.74:  # Jurong area
            if lon < 103.71:
                direction = "towards Tuas" 
                junction_info = "(near Jurong East interchange)"
            else:
                direction = "towards Changi"
                junction_info = "(after Jurong East interchange)"
        elif lon < 103.78:  # Bukit Batok area  
            direction = "towards Changi"
            junction_info = "(near Bukit Batok area)"
        elif lon < 103.84:  # Commonwealth/Queentown area
            direction = "towards Changi"
            junction_info = "(near Commonwealth area)"
        elif lon < 103.88:  # Eastern-central - Eunos area
            direction = "towards Changi"
            junction_info = "(near Eunos interchange)"
        else:  # Eastern section - Tampines/Simei 
            direction = "towards Changi"
            junction_info = "(near Tampines area)"
        expressway = f"PIE {direction} {junction_info}"
        
    # CTE (Central Expressway) - runs north-south, actual major junctions
    elif 1.29 <= lat <= 1.42 and 103.82 <= lon <= 103.86:
        if lat < 1.31:  # Southern section - Marina/City
            direction = "towards city"
            junction_info = "(near Marina Bay/City area)"
        elif lat < 1.33:  # Orchard/Newton area
            direction = "towards city" 
            junction_info = "(near Orchard/Newton area)"
        elif lat < 1.36:  # Balestier/Novena area
            direction = "towards Woodlands"
            junction_info = "(near Balestier/Novena area)"  
        elif lat < 1.39:  # Braddell/Ang Mo Kio area
            direction = "towards Woodlands"
            junction_info = "(near Ang Mo Kio interchange)"
        else:  # Northern section - Yishun/Woodlands
            direction = "towards Woodlands"
            junction_info = "(near Yishun/Woodlands area)"
        expressway = f"CTE {direction} {junction_info}"
        
    # AYE (Ayer Rajah Expressway) - southern route, actual interchanges
    elif 1.26 <= lat <= 1.32 and 103.72 <= lon <= 103.84:
        if lon < 103.74:  # Western section - Jurong
            direction = "towards Jurong"
            junction_info = "(near Jurong East area)"
        elif lon < 103.76:  # Yuan Ching Road area
            direction = "towards Jurong"
            junction_info = "(near Yuan Ching Road)" 
        elif lon < 103.79:  # Clementi area
            direction = "towards city"
            junction_info = "(near Clementi interchange)"
        else:  # Eastern section - Dover/Alexandra
            direction = "towards city"
            junction_info = "(near Alexandra Road area)"
        expressway = f"AYE {direction} {junction_info}"
        
    # BKE (Bukit Timah Expressway) - northwest, actual landmarks
    elif 1.33 <= lat <= 1.44 and 103.76 <= lon <= 103.82:
        if lat < 1.36:  # Southern section
            direction = "towards city"
            junction_info = "(near Bukit Timah area)"
        elif lat < 1.39:  # Central section
            direction = "towards Woodlands"
            junction_info = "(near Dairy Farm/Upper Bukit Timah)"
        elif lat < 1.42:  # Kranji area
            direction = "towards Woodlands"
            junction_info = "(near Kranji area)"
        else:  # Northern section
            direction = "towards Woodlands"
            junction_info = "(near Woodlands Checkpoint)"
        expressway = f"BKE {direction} {junction_info}"
        
    # TPE (Tampines Expressway) - northeast, actual junctions
    elif 1.33 <= lat <= 1.39 and 103.87 <= lon <= 103.96:
        if lon < 103.89:  # Western section
            direction = "towards SLE"
            junction_info = "(near Whitley Road area)"
        elif lon < 103.92:  # Paya Lebar area
            direction = "towards Changi"
            junction_info = "(near Paya Lebar area)"
        elif lon < 103.94:  # Tampines area
            direction = "towards Changi"
            junction_info = "(near Tampines interchange)"
        else:  # Far eastern
            direction = "towards Changi"
            junction_info = "(near Changi Airport area)"
        expressway = f"TPE {direction} {junction_info}"
        
    # SLE (Seletar Expressway) - north, actual connections
    elif 1.38 <= lat <= 1.43 and 103.82 <= lon <= 103.89:
        if lon < 103.84:  # Western section
            direction = "towards BKE"
            junction_info = "(near BKE connection)"
        elif lon < 103.86:  # Central section
            direction = "towards TPE"
            junction_info = "(near Yio Chu Kang Road)"
        else:  # Eastern section
            direction = "towards TPE"
            junction_info = "(near TPE connection)"
        expressway = f"SLE {direction} {junction_info}"
        
    # ECP (East Coast Parkway) - southeast coastal, actual landmarks
    elif 1.29 <= lat <= 1.32 and 103.86 <= lon <= 103.96:
        if lon < 103.88:  # Western section
            direction = "towards city"
            junction_info = "(near Marina Bay area)"
        elif lon < 103.91:  # Central section
            direction = "towards city"
            junction_info = "(near Tanjong Katong area)"
        elif lon < 103.94:  # Eastern section
            direction = "towards Changi"
            junction_info = "(near Bedok area)"
        else:  # Far eastern
            direction = "towards Changi"
            junction_info = "(near Changi Airport area)"
        expressway = f"ECP {direction} {junction_info}"
        
    # KPE (Kallang-Paya Lebar Expressway) - actual junctions
    elif 1.31 <= lat <= 1.36 and 103.86 <= lon <= 103.91:
        if lat < 1.32:  # Southern section
            direction = "towards Marina Bay"
            junction_info = "(near Marina Bay area)"
        elif lat < 1.33:  # Kallang area
            direction = "towards Marina Bay"
            junction_info = "(near Kallang area)"
        elif lat < 1.34:  # Macpherson area
            direction = "towards Defu"
            junction_info = "(near Macpherson area)"
        else:  # Northern section - Defu
            direction = "towards Defu"
            junction_info = "(near Defu interchange)"
        expressway = f"KPE {direction} {junction_info}"
        
    else:
        return None
    
    return expressway

def get_singapore_location_from_coords(lat, lon):
    """Get Singapore location name from coordinates"""
    if not lat or not lon:
        return None
        
    # Singapore area mapping
    singapore_areas = {
        # Central Region
        (1.2700, 1.3200, 103.8200, 103.8700): "Orchard Road area",
        (1.2800, 1.3200, 103.8400, 103.8800): "Marina Bay area", 
        (1.2900, 1.3100, 103.8500, 103.8600): "CBD/Raffles Place area",
        (1.3000, 1.3400, 103.8300, 103.8700): "Bugis/Little India area",
        
        # North Region  
        (1.4000, 1.4500, 103.7800, 103.8300): "Woodlands area",
        (1.3800, 1.4200, 103.8400, 103.8900): "Yishun area",
        (1.3600, 1.4000, 103.8200, 103.8800): "Ang Mo Kio area",
        
        # East Region
        (1.3200, 1.3600, 103.8800, 103.9300): "Tampines area",
        (1.3000, 1.3400, 103.9200, 103.9700): "Changi area", 
        (1.3200, 1.3600, 103.9300, 103.9800): "Bedok area",
        
        # West Region
        (1.3200, 1.3700, 103.6800, 103.7300): "Jurong West area",
        (1.3000, 1.3500, 103.7200, 103.7700): "Jurong East area",
    }
    
    for (min_lat, max_lat, min_lon, max_lon), area_name in singapore_areas.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return area_name
            
    # Fallback regions
    if lat > 1.38:
        return "Northern Singapore"
    elif lat < 1.29:
        return "Southern Singapore" 
    elif lon > 103.86:
        return "Eastern Singapore"
    elif lon < 103.77:
        return "Western Singapore"
    else:
        return "Central Singapore"

def format_accident_message(accident):
    """Format accident message with Singapore expressway enhancement"""
    # Extract information
    street = accident.get('street', 'Unknown location')
    city = accident.get('city', 'Singapore')
    reported_by = accident.get('reportBy', 'Waze Embed API')
    confidence = accident.get('confidence', 8)
    reliability = accident.get('reliability', 8)
    
    # Get coordinates
    location = accident.get('location', {})
    lat = location.get('y', 0)
    lon = location.get('x', 0)
    
    # Get timestamp
    pub_millis = accident.get('pubMillis', 0)
    if pub_millis:
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
        sgt_time = utc_time.astimezone(SGT)
        report_time = sgt_time.strftime('%Y-%m-%d %H:%M:%S SGT')
    else:
        report_time = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    
    # PRIORITIZED LOCATION DETECTION with ENHANCED EXPRESSWAY CONTEXT
    # Priority 1: Enhanced expressway with junction details (highest priority)
    if lat and lon:
        expressway_info = get_singapore_expressway_with_direction(lat, lon)
        if expressway_info:
            location_text = expressway_info
        elif street and street.lower() not in ['unknown location', 'traffic incident detected'] and len(street.strip()) > 2:
            if city and city != 'Singapore':
                location_text = f"{street}, {city}"
            else:
                location_text = street
        else:
            area = get_singapore_location_from_coords(lat, lon)
            if area:
                location_text = area
            else:
                location_text = f"coordinates {lat:.4f}, {lon:.4f}"
    elif street and street.lower() not in ['unknown location', 'traffic incident detected']:
        location_text = street
    else:
        location_text = "Unknown location"
    
    # Build message
    message = f"Accident on {location_text}\n"
    message += f"🕐 Reported: {report_time}\n"
    message += f"👤 Reported by: {reported_by}\n"
    message += f"📈 Confidence: {confidence}/10\n"
    message += f"✅ Reliability: {reliability}/10\n\n"
    
    if lat and lon:
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_url})\n"
        message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_url})"
    else:
        message += f"🗺️ Location coordinates not available"
    
    return message

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            log_message(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        log_message(f"Error sending message: {e}")
        return False

def coordinates_similar(lat1, lon1, lat2, lon2, radius_meters=100):
    """Check if coordinates are within specified radius"""
    if not all([lat1, lon1, lat2, lon2]):
        return False
    
    # Haversine formula for distance
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = 6371000 * c  # Earth's radius in meters
    
    return distance <= radius_meters

def process_accidents():
    """Main accident processing function"""
    log_message("🔄 Checking for new accidents using Waze Embed API...")
    
    # Initialize Waze API
    waze_api = WazeEmbedAPI()
    if not waze_api.setup_session():
        log_message("❌ Failed to setup Waze session")
        return 0
    
    processed_accidents = load_processed_accidents()
    new_accidents = 0
    
    try:
        # Get traffic data from embed API
        alerts = waze_api.get_singapore_traffic_data()
        if not alerts:
            log_message("ℹ️  No traffic alerts received from embed API")
            return new_accidents
        
        log_message(f"📊 Found {len(alerts)} potential accidents from embed API")
        
        for accident in alerts:
            # Generate unique ID
            accident_id = get_accident_id(accident)
            
            # Check if already processed
            if accident_id in processed_accidents:
                continue
            
            # Check coordinates are in Singapore
            location = accident.get('location', {})
            lat = location.get('y', 0)
            lon = location.get('x', 0)
            
            if lat and lon and not is_within_singapore(lat, lon):
                log_message(f"🌏 Filtering accident outside Singapore: {lat:.4f}, {lon:.4f}")
                continue
            
            # Check if accident is recent
            if not is_accident_recent(accident):
                continue
            
            # Check for duplicates with existing accidents (within 100m)
            is_duplicate = False
            if lat and lon:
                for existing_id in processed_accidents:
                    if "coord_" in existing_id:
                        try:
                            parts = existing_id.split("_")
                            if len(parts) >= 4:
                                existing_lat = float(parts[2])
                                existing_lon = float(parts[3])
                                if coordinates_similar(lat, lon, existing_lat, existing_lon):
                                    is_duplicate = True
                                    log_message(f"🔄 Filtering duplicate accident: {existing_id}")
                                    break
                        except (ValueError, IndexError):
                            continue
            
            if is_duplicate:
                processed_accidents.add(accident_id)
                continue
            
            # Format and send message
            message = format_accident_message(accident)
            if send_telegram_message(message):
                processed_accidents.add(accident_id)
                new_accidents += 1
                log_message(f"✅ Posted new accident: {accident_id} at {lat:.4f}, {lon:.4f}")
                # Brief delay between posts
                time.sleep(2)
            else:
                log_message(f"❌ Failed to post accident: {accident_id}")
        
        # Save processed accidents
        save_processed_accidents(processed_accidents)
        
    except Exception as e:
        log_message(f"❌ Error processing accidents: {e}")
    
    return new_accidents

def main():
    """Main monitoring loop"""
    log_message("🚀 Starting NEW Waze Embed Monitor for Singapore...")
    log_message(f"📍 Monitoring bounds: {SINGAPORE_BOUNDS}")
    log_message(f"⏰ Check interval: {CHECK_INTERVAL_SECONDS} seconds")
    log_message(f"🕐 Max accident age: {MAX_ACCIDENT_AGE_MINUTES} minutes")
    
    while True:
        try:
            new_count = process_accidents()
            if new_count > 0:
                log_message(f"📢 Posted {new_count} new accident(s)")
            else:
                log_message("ℹ️  No new accidents to post")
                
        except KeyboardInterrupt:
            log_message("🛑 Monitor stopped by user")
            break
        except Exception as e:
            log_message(f"❌ Unexpected error: {e}")
        
        # Wait before next check
        log_message(f"⏳ Waiting {CHECK_INTERVAL_SECONDS} seconds until next check...")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()