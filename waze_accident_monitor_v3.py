#!/usr/bin/env python3
"""
Advanced Anti-Blocking Waze Monitor with Proxy Support and Alternative Sources
Version 3.0 - Multi-source accident monitoring
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

# Enhanced User Agents with more variety
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"
]

# Free proxy services (for testing - in production use premium proxies)
FREE_PROXIES = [
    # Add working free proxies here if available
    # Format: {"http": "http://proxy:port", "https": "https://proxy:port"}
    # Note: Free proxies are unreliable, consider premium services for production
]

def log_message(message: str) -> None:
    """Print timestamped log message"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def get_random_headers() -> Dict[str, str]:
    """Get random headers to simulate different browsers"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

def try_with_proxy(url: str, params: dict, proxies: dict = None, timeout: int = 10) -> Optional[requests.Response]:
    """Try request with optional proxy"""
    headers = get_random_headers()
    
    try:
        response = requests.get(
            url, 
            params=params, 
            headers=headers, 
            proxies=proxies,
            timeout=timeout,
            verify=True,
            allow_redirects=True
        )
        return response
    except Exception as e:
        log_message(f"Request failed: {e}")
        return None

def get_alternative_traffic_data() -> List[Dict]:
    """No alternative sources - focusing on Waze and @sgaccident only"""
    log_message("Alternative sources disabled - using only Waze and @sgaccident")
    return []
    
    # Alternative 3: Try web scraping traffic websites
    try:
        log_message("Trying traffic website scraping...")
        # Example: EMAS (Emergency Monitoring & Advisory System)
        traffic_sites = [
            "https://www.emas.gov.sg",
            "https://www.onemotoring.com.sg"
        ]
        
        for site in traffic_sites:
            response = try_with_proxy(site, {})
            if response and response.status_code == 200:
                log_message(f"Successfully accessed {site}")
                # Parse HTML for accident information
                
    except Exception as e:
        log_message(f"Web scraping failed: {e}")
    
    return accidents

def get_waze_accidents() -> List[Dict]:
    """Enhanced Waze accident fetching with multiple bypass strategies"""
    log_message("Fetching Waze accidents with enhanced anti-blocking...")
    
    singapore_params = {
        'bottom': '1.1304',
        'top': '1.4784',
        'left': '103.5000',
        'right': '104.1000',
        'env': 'row',
        'types': 'alerts'
    }
    
    # Strategy 1: Try different Waze endpoints
    waze_endpoints = [
        'https://www.waze.com/live-map/api/georss',
        'https://www.waze.com/live-map/api/georss/alerts',
        'https://www.waze.com/rtserver/web/TGeoRSS'
    ]
    
    for endpoint in waze_endpoints:
        log_message(f"Trying Waze endpoint: {endpoint}")
        
        # Strategy 2: Try with different proxies if available
        proxy_attempts = [None] + FREE_PROXIES  # None = no proxy, then try proxies
        
        for proxy in proxy_attempts:
            if proxy:
                log_message(f"Using proxy: {list(proxy.values())[0]}")
            
            response = try_with_proxy(endpoint, singapore_params, proxy)
            
            if response and response.status_code == 200:
                log_message(f"✓ Waze API success with status 200")
                try:
                    # Parse response content for accidents
                    accidents = parse_waze_response(response.text)
                    log_message(f"Found {len(accidents)} accidents from Waze")
                    return accidents
                except Exception as e:
                    log_message(f"Error parsing Waze response: {e}")
            
            elif response:
                log_message(f"Waze API returned status {response.status_code}")
                
            # Random delay between attempts
            time.sleep(random.uniform(2, 5))
    
    log_message("All Waze endpoints failed, trying alternative sources...")
    return get_alternative_traffic_data()

def parse_waze_response(response_text: str) -> List[Dict]:
    """Parse Waze response for accident information"""
    accidents = []
    
    try:
        # If JSON response
        if response_text.strip().startswith('{') or response_text.strip().startswith('['):
            data = json.loads(response_text)
            if isinstance(data, dict) and 'alerts' in data:
                for alert in data['alerts']:
                    if alert.get('type') == 'ACCIDENT' or 'accident' in alert.get('subtype', '').lower():
                        accidents.append({
                            'id': alert.get('uuid', ''),
                            'location': f"{alert.get('location', {}).get('y', 0)},{alert.get('location', {}).get('x', 0)}",
                            'description': alert.get('reportDescription', 'Accident reported'),
                            'street': alert.get('street', 'Unknown location'),
                            'city': alert.get('city', 'Singapore'),
                            'timestamp': datetime.datetime.now().isoformat()
                        })
        
        # If XML/RSS response
        elif 'xml' in response_text.lower() or 'rss' in response_text.lower():
            # Basic XML parsing for accident items
            if 'accident' in response_text.lower():
                log_message("Found accident mentions in XML response")
                # Simple regex parsing for now
                import re
                accident_pattern = r'<item[^>]*>.*?accident.*?</item>'
                matches = re.findall(accident_pattern, response_text, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    accidents.append({
                        'id': str(hash(match)),
                        'description': 'Accident reported via Waze XML',
                        'location': 'Singapore',
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                    
    except Exception as e:
        log_message(f"Error parsing Waze response: {e}")
    
    return accidents

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

def is_valid_singapore_coordinates(lat: float, lon: float) -> bool:
    """Check if coordinates are within Singapore bounds"""
    return (1.1304 <= lat <= 1.4784) and (103.5000 <= lon <= 104.1000)

def format_accident_message(accident: Dict, source: str = "Waze") -> str:
    """Format accident information for Telegram"""
    timestamp = datetime.datetime.now().strftime("%H:%M")
    
    location = accident.get('street', accident.get('location', 'Unknown location'))
    description = accident.get('description', 'Accident reported')
    
    message = f"🚨 **ACCIDENT ALERT** ({source})\n"
    message += f"📍 **Location:** {location}\n"
    message += f"📝 **Details:** {description}\n"
    message += f"⏰ **Time:** {timestamp}\n"
    message += f"🤖 **Source:** {source} Monitor"
    
    return message

def process_waze_accidents() -> None:
    """Process new accidents from Waze API"""
    try:
        accidents = get_waze_accidents()
        waze_processed, telegram_processed = load_processed_accidents()
        new_count = 0
        
        for accident in accidents:
            accident_id = accident.get('id', str(hash(str(accident))))
            
            if accident_id in waze_processed:
                continue
            
            # Filter out Malaysia-related accidents
            accident_text = f"{accident.get('description', '')} {accident.get('street', '')} {accident.get('location', '')}"
            if contains_malaysia_keywords(accident_text):
                log_message(f"Skipping Malaysia-related accident: {accident.get('street', 'Unknown')}")
                waze_processed.add(accident_id)
                continue
            
            # Send to Telegram
            message = format_accident_message(accident, "Waze")
            if send_telegram_message(message, "Markdown"):
                waze_processed.add(accident_id)
                new_count += 1
                log_message(f"✓ New Waze accident posted: {accident.get('street', 'Unknown location')}")
                time.sleep(2)  # Avoid rapid posting
        
        save_processed_accidents(waze_processed, telegram_processed)
        if new_count > 0:
            log_message(f"Posted {new_count} new Waze accidents")
            
    except Exception as e:
        log_message(f"Error processing Waze accidents: {e}")

def get_telegram_updates() -> List[Dict]:
    """Get updates from @sgaccident channel with enhanced error handling"""
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
    log_message(f"Monitoring: Waze API + @sgaccident channel")
    log_message(f"Target channel: {CHAT_ID}")
    log_message(f"Simplified sources: Waze API with anti-blocking + @sgaccident")
    
    while True:
        try:
            # Process both sources
            process_waze_accidents()
            process_sgaccident_updates()
            
            # Clean up old processed accidents (keep last 1000)
            waze_processed, telegram_processed = load_processed_accidents()
            if len(waze_processed) > 1000:
                waze_processed = set(list(waze_processed)[-500:])
            if len(telegram_processed) > 1000:
                telegram_processed = set(list(telegram_processed)[-500:])
            save_processed_accidents(waze_processed, telegram_processed)
            
            # Randomized sleep to avoid detection (90-150 seconds)
            sleep_time = random.randint(90, 150)
            log_message(f"Advanced monitoring cycle complete, sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            log_message("Monitoring stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            # Random sleep on error to avoid rapid retries
            error_sleep = random.randint(180, 300)
            log_message(f"Waiting {error_sleep} seconds after error...")
            time.sleep(error_sleep)

if __name__ == "__main__":
    main()