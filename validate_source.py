#!/usr/bin/env python3
"""
Test script to identify if posts are coming from PC or Cloud
"""
import requests
import socket
import platform
from datetime import datetime
import pytz

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHANNEL_ID = "-1003683261194"

def get_system_info():
    """Get system information to identify the source"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Try to get public IP
        try:
            public_ip = requests.get('https://ipinfo.io/ip', timeout=5).text.strip()
        except:
            public_ip = "Unknown"
            
        system_info = {
            'hostname': hostname,
            'local_ip': local_ip,
            'public_ip': public_ip,
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'system': platform.system()
        }
        return system_info
    except Exception as e:
        return {'error': str(e)}

def send_test_message():
    """Send a test message to identify the source"""
    singapore_tz = pytz.timezone('Asia/Singapore')
    timestamp = datetime.now(singapore_tz).strftime('%Y-%m-%d %H:%M:%S SGT')
    
    system_info = get_system_info()
    
    test_message = f"""🔍 **SYSTEM VALIDATION TEST**

⏰ **Time:** {timestamp}

🖥️ **System Info:**
• Hostname: {system_info.get('hostname', 'Unknown')}
• Local IP: {system_info.get('local_ip', 'Unknown')} 
• Public IP: {system_info.get('public_ip', 'Unknown')}
• Platform: {system_info.get('system', 'Unknown')}
• Python: {system_info.get('python_version', 'Unknown')}

📍 **Source Detection:**
• If hostname shows "USER-PC" or similar → **Running from your PC**
• If hostname shows "gce-" or similar → **Running from Google Cloud**
• If public IP is your home IP → **Running from your PC**
• If public IP is Google Cloud range → **Running from Cloud**

🎯 **This message confirms which system is posting to your channel**

*Test completed - this message can be deleted*"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_ID,
        'text': test_message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ TEST MESSAGE SENT SUCCESSFULLY!")
                print(f"📱 Message ID: {result['result']['message_id']}")
                print(f"🎯 Check your channel: https://web.telegram.org/a/#-1003683261194")
                print("\n📊 SYSTEM DETECTION RESULTS:")
                for key, value in system_info.items():
                    print(f"   {key}: {value}")
                
                # Analyze the source
                hostname = system_info.get('hostname', '').lower()
                if 'user' in hostname or 'pc' in hostname or 'desktop' in hostname:
                    print("\n🖥️  **DETECTED: Running from your PC**")
                elif 'gce' in hostname or 'google' in hostname or 'cloud' in hostname:
                    print("\n☁️  **DETECTED: Running from Google Cloud**")
                else:
                    print(f"\n❓ **UNCLEAR: Check hostname '{hostname}' in the message**")
                    
                return True
            else:
                print(f"❌ Telegram API error: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

if __name__ == "__main__":
    print("🔍 VALIDATION TEST - Identifying posting source...")
    print("=" * 50)
    
    if send_test_message():
        print("\n🎉 Test complete! Check the message in your channel to see the source.")
    else:
        print("\n❌ Test failed. Check your configuration.")