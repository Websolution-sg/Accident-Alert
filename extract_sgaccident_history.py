#!/usr/bin/env python3
"""
Extract last 5 accident posts from @sgaccident and repost to target channel
One-time extraction script
"""
import requests
import json
import time
import datetime
import re

# Configuration
TELEGRAM_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SOURCE_CHANNEL = "-1001486947378"  # @sgaccident
TARGET_CHANNEL = "-1003683261194"  # Your channel

def log_message(message):
    """Print timestamped log message"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_channel_history():
    """Get recent messages from @sgaccident channel"""
    log_message("Fetching recent messages from @sgaccident channel...")
    
    try:
        # Try different methods to get channel messages
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {'limit': 100, 'timeout': 5}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                log_message(f"Retrieved {len(updates)} total updates")
                
                # Filter for @sgaccident channel posts
                channel_posts = []
                for update in updates:
                    if 'channel_post' in update:
                        post = update['channel_post']
                        chat = post.get('chat', {})
                        
                        if str(chat.get('id')) == SOURCE_CHANNEL:
                            channel_posts.append(post)
                
                log_message(f"Found {len(channel_posts)} posts from @sgaccident")
                return channel_posts
            else:
                log_message(f"Telegram API error: {data.get('description')}")
        else:
            log_message(f"HTTP error: {response.status_code}")
            
    except Exception as e:
        log_message(f"Error fetching updates: {e}")
    
    return []

def is_accident_related(text):
    """Check if text is accident-related"""
    if not text:
        return False
    
    accident_keywords = [
        'accident', 'crash', 'collision', 'jam', 'blocked', 'closure',
        'emergency', 'incident', 'breakdown', 'stalled', 'congestion'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in accident_keywords)

def extract_coordinates_from_text(text):
    """Extract coordinates from message text"""
    if not text:
        return None, None
    
    # Look for coordinate patterns
    patterns = [
        r'(\d+\.\d+),\s*(\d+\.\d+)',  # Basic decimal coordinates
        r'maps\.google\.com[^\s]*[@,](-?\d+\.\d+),(-?\d+\.\d+)',  # Google Maps
        r'waze\.com[^\s]*ll=(-?\d+\.\d+),(-?\d+\.\d+)'  # Waze links
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                lat, lon = float(match.group(1)), float(match.group(2))
                # Validate Singapore coordinates
                if 1.0 <= lat <= 1.5 and 103.6 <= lon <= 104.1:
                    return lat, lon
            except (ValueError, IndexError):
                continue
    
    return None, None

def format_repost_message(original_text, post_date, lat=None, lon=None):
    """Format the message for reposting"""
    message = f"🚨 <b>ACCIDENT ALERT</b> (@sgaccident)\n\n"
    message += f"📍 <b>Details:</b>\n{original_text}\n\n"
    message += f"⏰ <b>Originally Posted:</b> {post_date}\n"
    message += f"🔄 <b>Reposted:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if lat and lon:
        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ <a href='{google_maps_link}'>View on Google Maps</a>\n"
        message += f"🚗 <a href='{waze_link}'>Open in Waze</a>\n\n"
    
    message += f"🔗 <b>Source:</b> @sgaccident (Historical)"
    
    return message

def send_telegram_message(message):
    """Send message to target channel"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TARGET_CHANNEL,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            log_message(f"Failed to send message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(f"Error sending message: {e}")
        return False

def main():
    """Extract last 5 accident posts and repost them"""
    log_message("=" * 60)
    log_message("EXTRACTING LAST 5 ACCIDENT POSTS FROM @SGACCIDENT")
    log_message("=" * 60)
    log_message(f"Source: https://web.telegram.org/a/#-1001486947378")
    log_message(f"Target: https://web.telegram.org/a/#-1003683261194")
    log_message("")
    
    # Get recent channel posts
    posts = get_channel_history()
    
    if not posts:
        log_message("❌ No posts found from @sgaccident channel")
        log_message("Note: Bot may not have access to channel history")
        return
    
    # Filter for accident-related posts
    accident_posts = []
    for post in posts:
        text = post.get('text', '')
        if text and is_accident_related(text):
            accident_posts.append(post)
    
    log_message(f"Found {len(accident_posts)} accident-related posts")
    
    if not accident_posts:
        log_message("❌ No accident-related posts found in recent messages")
        return
    
    # Get last 5 accident posts (most recent first)
    last_5_posts = accident_posts[-5:]  # Take last 5
    last_5_posts.reverse()  # Most recent first
    
    log_message(f"Processing last {len(last_5_posts)} accident posts...")
    log_message("")
    
    posted_count = 0
    
    for i, post in enumerate(last_5_posts, 1):
        text = post.get('text', '')
        post_date = datetime.datetime.fromtimestamp(post.get('date', 0)).strftime('%Y-%m-%d %H:%M:%S')
        
        log_message(f"Post {i}: {text[:50]}...")
        log_message(f"Original date: {post_date}")
        
        # Extract coordinates if available
        lat, lon = extract_coordinates_from_text(text)
        if lat and lon:
            log_message(f"Coordinates found: {lat:.4f}, {lon:.4f}")
        
        # Format and send message
        formatted_message = format_repost_message(text, post_date, lat, lon)
        
        if send_telegram_message(formatted_message):
            log_message(f"✅ Successfully reposted post {i}")
            posted_count += 1
        else:
            log_message(f"❌ Failed to repost post {i}")
        
        log_message("")
        
        # Wait between posts to avoid rate limiting
        if i < len(last_5_posts):
            time.sleep(3)
    
    log_message("=" * 60)
    log_message(f"EXTRACTION COMPLETE: {posted_count}/{len(last_5_posts)} posts reposted")
    log_message("=" * 60)
    
    if posted_count == 0:
        log_message("⚠️  No posts were successfully reposted")
        log_message("This might be due to:")
        log_message("1. Bot doesn't have access to channel history")
        log_message("2. No recent accident posts in the available updates")
        log_message("3. Network or API issues")
        log_message("")
        log_message("💡 Try running the regular monitoring script to catch new posts:")
        log_message("   python waze_accident_monitor.py")

if __name__ == "__main__":
    main()