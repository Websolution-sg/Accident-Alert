#!/usr/bin/env python3
"""
Singapore Accident Monitor with Working Government APIs
Version 4.0 - Multi-source with Singapore.gov APIs
"""
import requests
import json
import time
import datetime
import os
import re
import sys
import random
from typing import Dict, List, Optional, Tuple

# Configure output to flush immediately
sys.stdout.reconfigure(line_buffering=True)

# Configuration
TELEGRAM_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"  # Target channel
SG_ACCIDENT_CHANNEL = "-1001486947378"  # @sgaccident channel

# Data storage files
PROCESSED_FILE = "processed_accidents.json"
OFFSET_FILE = "telegram_offset.json"
TRAFFIC_CACHE = "traffic_cache.json"

# Enhanced User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
]

def log_message(message: str) -> None:
    """Print timestamped log message"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

# Removed government API function - focusing on Waze and @sgaccident only
                
        else:
            log_message(f"Traffic cameras API failed: {response.status_code}")
            
    except Exception as e:
        log_message(f"Error fetching traffic cameras: {e}")
    
    return []

# Removed taxi availability function - focusing on Waze and @sgaccident only
        
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            
            if features:
                # Load previous taxi data for comparison
                prev_data = load_traffic_cache()
                current_time = datetime.datetime.now().isoformat()
                
                # Count taxis in different areas
                total_taxis = len(features)
                log_message(f"✓ Found {total_taxis} available taxis")
                
                # Simple heuristic: Very few taxis in an area might indicate congestion/incident
                # Group taxis by approximate areas
                area_counts = {}
                for feature in features:
                    coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                    if len(coords) >= 2:
                        # Group into approximate grid areas
                        lat_grid = int(coords[1] * 100) / 100  # Round to 2 decimal places
                        lon_grid = int(coords[0] * 100) / 100
                        area_key = f"{lat_grid},{lon_grid}"
                        area_counts[area_key] = area_counts.get(area_key, 0) + 1
                
                # Compare with historical data to detect anomalies
                anomalies = []
                prev_taxi_counts = prev_data.get('taxi_areas', {})
                
                for area, count in area_counts.items():
                    prev_count = prev_taxi_counts.get(area, count)
                    
                    # If current count is significantly lower than before, might indicate incident
                    if prev_count > 0 and count < prev_count * 0.3:  # 70% reduction
                        coords_parts = area.split(',')
                        if len(coords_parts) == 2:
                            anomalies.append({
                                'id': f"taxi_anomaly_{area}",
                                'location': area,
                                'description': f"Significant taxi availability drop in area {area} (was {prev_count}, now {count})",
                                'timestamp': current_time,
                                'source': 'taxi_availability',
                                'severity': 'medium'
                            })
                
                # Update cache
                save_traffic_cache({
                    'taxi_areas': area_counts,
                    'last_updated': current_time,
                    'total_taxis': total_taxis
                })
                
                if anomalies:
                    log_message(f"✓ Detected {len(anomalies)} taxi availability anomalies")
                
                return anomalies
                
        else:
            log_message(f"Taxi availability API failed: {response.status_code}")
            
    except Exception as e:
        log_message(f"Error analyzing taxi availability: {e}")
    
    return []

def load_traffic_cache() -> Dict:
    """Load cached traffic data for comparison"""
    try:
        with open(TRAFFIC_CACHE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_traffic_cache(data: Dict) -> None:
    """Save traffic data cache"""
    try:
        with open(TRAFFIC_CACHE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_message(f"Error saving traffic cache: {e}")

# Removed police website scraping - focusing on Waze and @sgaccident only
    
    try:
        url = "https://www.police.gov.sg"
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Look for traffic-related content
            traffic_indicators = [
                'traffic accident', 'road closure', 'traffic incident',
                'accident report', 'traffic alert', 'road works'
            ]
            
            incidents = []
            for indicator in traffic_indicators:
                if indicator in content:
                    # Simple extraction - in production, use proper HTML parsing
                    incidents.append({
                        'id': f"police_{hash(indicator + str(datetime.datetime.now().date()))}",
                        'description': f"Traffic update containing '{indicator}' found on police website",
                        'location': 'Singapore',
                        'timestamp': datetime.datetime.now().isoformat(),
                        'source': 'police_website',
                        'url': url
                    })
            
            if incidents:
                log_message(f"✓ Found {len(incidents)} potential traffic updates on police website")
            
            return incidents
            
    except Exception as e:
        log_message(f"Error scraping police website: {e}")
    
    return []

# Removed alternative traffic data function - using only Waze and @sgaccident

def attempt_waze_with_delay() -> List[Dict]:
    """Try Waze API with extended delays and different approaches"""
    log_message("Attempting Waze API with anti-blocking measures...")
    
    # Long delay before trying
    delay = random.randint(30, 60)
    log_message(f"Waiting {delay} seconds before Waze attempt...")
    time.sleep(delay)
    
    waze_endpoints = [
        'https://www.waze.com/live-map/api/georss',
        'https://www.waze.com/row-georss',  # Alternative endpoint
    ]
    
    singapore_params = {
        'bottom': '1.1304',
        'top': '1.4784',
        'left': '103.5000',
        'right': '104.1000',
        'env': 'row',
        'types': 'alerts'
    }
    
    for endpoint in waze_endpoints:
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache'
            }
            
            log_message(f"Trying Waze endpoint: {endpoint}")
            response = requests.get(endpoint, params=singapore_params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                log_message(f"✓ Waze API success! Content length: {len(response.text)}")
                # Parse the response - could be JSON or XML
                try:
                    if response.text.strip().startswith('{'):
                        data = response.json()
                        log_message("Got JSON response from Waze")
                        return []  # Parse JSON format here
                    else:
                        log_message("Got non-JSON response from Waze")
                        # Could be XML/RSS format
                        return []  # Parse XML format here
                except:
                    log_message("Could not parse Waze response")
                    
            else:
                log_message(f"Waze API returned {response.status_code}")
                
        except Exception as e:
            log_message(f"Waze attempt failed: {e}")
        
        # Delay between endpoints
        time.sleep(random.randint(10, 20))
    
    log_message("All Waze attempts failed, relying on government sources")
    return []

def load_processed_accidents() -> Tuple[set, set]:
    """Load processed accident IDs from file"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('waze', [])), set(data.get('telegram', []))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return set(), set()

def save_processed_accidents(waze_processed: set, telegram_processed: set) -> None:
    """Save processed accident IDs to file"""
    data = {
        'waze': list(waze_processed),
        'telegram': list(telegram_processed)
    }
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_telegram_message(message: str, parse_mode: str = None) -> bool:
    """Send message to Telegram channel"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': message
        }
        if parse_mode:
            data['parse_mode'] = parse_mode
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            log_message("✓ Message sent successfully")
            return True
        else:
            log_message(f"✗ Telegram API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(f"✗ Error sending message: {e}")
        return False

def contains_malaysia_keywords(text: str) -> bool:
    """Check if text contains Malaysia-related keywords to filter out"""
    malaysia_keywords = [
        'malaysia', 'kuala lumpur', 'kl', 'selangor', 'penang', 'johor',
        'perak', 'kedah', 'kelantan', 'terengganu', 'pahang', 'negeri sembilan',
        'melaka', 'malacca', 'sabah', 'sarawak', 'putrajaya', 'labuan'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in malaysia_keywords)

def format_accident_message(incident: Dict, source: str = "Government") -> str:
    """Format incident information for Telegram"""
    timestamp = datetime.datetime.now().strftime("%H:%M")
    
    location = incident.get('location', 'Singapore')
    description = incident.get('description', 'Traffic incident detected')
    severity = incident.get('severity', 'medium')
    
    # Choose emoji based on source and severity
    if source.lower() in ['waze', 'sgaccident']:
        emoji = "🚨"
    elif 'camera' in source.lower():
        emoji = "📹"
    elif 'taxi' in source.lower():
        emoji = "🚕"
    elif 'police' in source.lower():
        emoji = "🚔"
    else:
        emoji = "⚠️"
    
    message = f"{emoji} **TRAFFIC ALERT** ({source})\n"
    message += f"📍 **Location:** {location}\n"
    message += f"📝 **Details:** {description}\n"
    message += f"⏰ **Time:** {timestamp}\n"
    message += f"🤖 **Source:** {source} Monitor"
    
    if incident.get('url'):
        message += f"\n🔗 **Reference:** {incident['url']}"
    
    return message

def process_waze_data() -> None:
    """Process incidents from Waze only"""
    try:
        # Try Waze with anti-blocking measures
        waze_incidents = attempt_waze_with_delay()
        
        # Use only Waze data
        all_incidents = waze_incidents
        
        waze_processed, telegram_processed = load_processed_accidents()
        new_count = 0
        
        for incident in all_incidents:
            incident_id = incident.get('id', str(hash(str(incident))))
            
            if incident_id in waze_processed:
                continue
            
            # Filter out Malaysia-related incidents
            incident_text = f"{incident.get('description', '')} {incident.get('location', '')}"
            if contains_malaysia_keywords(incident_text):
                log_message(f"Skipping Malaysia-related incident: {incident.get('location', 'Unknown')}")
                waze_processed.add(incident_id)
                continue
            
            # Only post significant incidents to avoid spam
            source = incident.get('source', 'Government')
            severity = incident.get('severity', 'medium')
            
            # Filter by severity - only post medium/high severity incidents
            if severity in ['medium', 'high']:
                message = format_accident_message(incident, source.title())
                if send_telegram_message(message, "Markdown"):
                    waze_processed.add(incident_id)
                    new_count += 1
                    log_message(f"✓ New {source} incident posted: {incident.get('location', 'Unknown')}")
                    time.sleep(3)  # Avoid rapid posting
            else:
                # Mark as processed but don't post low-severity items
                waze_processed.add(incident_id)
        
        save_processed_accidents(waze_processed, telegram_processed)
        if new_count > 0:
            log_message(f"Posted {new_count} new government incidents")
            
    except Exception as e:
        log_message(f"Error processing government data: {e}")

def get_telegram_updates() -> List[Dict]:
    """Get updates from @sgaccident channel"""
    try:
        # Load last offset
        offset = 0
        try:
            with open(OFFSET_FILE, 'r') as f:
                offset = json.load(f).get('offset', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {'offset': offset + 1, 'limit': 100}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                
                # Update offset
                if updates:
                    last_update_id = updates[-1]['update_id']
                    with open(OFFSET_FILE, 'w') as f:
                        json.dump({'offset': last_update_id}, f)
                
                return updates
            else:
                log_message(f"Telegram API error: {data.get('description', 'Unknown error')}")
                return []
        else:
            log_message(f"Failed to get Telegram updates: {response.status_code}")
            return []
            
    except Exception as e:
        log_message(f"Error getting Telegram updates: {e}")
        return []

def process_sgaccident_updates() -> None:
    """Process new messages from @sgaccident channel"""
    try:
        updates = get_telegram_updates()
        waze_processed, telegram_processed = load_processed_accidents()
        new_count = 0
        
        for update in updates:
            if 'channel_post' not in update:
                continue
                
            post = update['channel_post']
            chat = post.get('chat', {})
            
            # Check if it's from @sgaccident channel
            if str(chat.get('id')) != SG_ACCIDENT_CHANNEL:
                continue
            
            message_id = str(post.get('message_id', ''))
            text = post.get('text', '')
            
            if not text or message_id in telegram_processed:
                continue
            
            # Check for accident keywords
            accident_keywords = ['accident', 'crash', 'collision', 'jam', 'block', 'emergency']
            if not any(keyword.lower() in text.lower() for keyword in accident_keywords):
                continue
            
            # Filter out Malaysia-related content
            if contains_malaysia_keywords(text):
                log_message(f"Skipping Malaysia-related @sgaccident post")
                telegram_processed.add(message_id)
                continue
            
            # Forward to our channel
            forward_message = f"🚨 **ACCIDENT ALERT** (SGAccident)\n\n{text}\n\n🤖 **Source:** @sgaccident Monitor"
            
            if send_telegram_message(forward_message, "Markdown"):
                telegram_processed.add(message_id)
                new_count += 1
                log_message(f"✓ Forwarded @sgaccident update")
                time.sleep(2)  # Avoid rapid posting
        
        save_processed_accidents(waze_processed, telegram_processed)
        if new_count > 0:
            log_message(f"Forwarded {new_count} new @sgaccident updates")
            
    except Exception as e:
        log_message(f"Error processing @sgaccident updates: {e}")

def main():
    """Main monitoring loop with Waze and @sgaccident only"""
    log_message("Starting accident monitoring with Waze and @sgaccident...")
    log_message(f"Data sources: Waze API + @sgaccident channel")
    log_message(f"Target channel: {CHAT_ID}")
    
    while True:
        try:
            # Process both sources
            process_waze_data()           # Waze API only
            process_sgaccident_updates()  # @sgaccident channel
            
            # Clean up old processed incidents (keep last 1000)
            waze_processed, telegram_processed = load_processed_accidents()
            if len(waze_processed) > 1000:
                waze_processed = set(list(waze_processed)[-500:])
            if len(telegram_processed) > 1000:
                telegram_processed = set(list(telegram_processed)[-500:])
            save_processed_accidents(waze_processed, telegram_processed)
            
            # Extended sleep for government APIs (they don't update as frequently)
            sleep_time = random.randint(180, 240)  # 3-4 minutes
            log_message(f"Government monitoring cycle complete, sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            log_message("Monitoring stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            # Random sleep on error
            error_sleep = random.randint(300, 600)  # 5-10 minutes
            log_message(f"Waiting {error_sleep} seconds after error...")
            time.sleep(error_sleep)

if __name__ == "__main__":
    main()