#!/usr/bin/env python3
"""
Check monitoring status and restart if needed
"""
import asyncio
import requests
import datetime
from telethon import TelegramClient

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_FILE = "pukiboi_session"
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHAT_ID = "-1003683261194"
SGACCIDENT_CHANNEL_ID = -1001486947378

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] CHECK: {message}", flush=True)

def send_status_message(message):
    """Send status message via bot"""
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={'chat_id': TARGET_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            log_message(f"Status message sent (ID: {result['result']['message_id']})")
        else:
            log_message(f"Failed to send status: {response.status_code}")
    except Exception as e:
        log_message(f"Error sending status: {e}")

async def test_telethon_connection():
    """Test if Telethon can connect and access channels"""
    try:
        client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        await client.start()
        
        # Test authentication
        me = await client.get_me()
        log_message(f"✅ Telethon authenticated as: {me.first_name} (@{me.username})")
        
        # Test channel access
        sgaccident_entity = await client.get_entity(SGACCIDENT_CHANNEL_ID)
        target_entity = await client.get_entity(TARGET_CHAT_ID)
        
        log_message(f"✅ Source channel accessible: {sgaccident_entity.title}")
        log_message(f"✅ Target channel accessible: {target_entity.title}")
        
        # Get recent messages from source to test
        messages = await client.get_messages(SGACCIDENT_CHANNEL_ID, limit=5)
        log_message(f"✅ Retrieved {len(messages)} recent messages from @sgaccident")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        log_message(f"❌ Telethon test failed: {e}")
        return False

async def main():
    """Main check function"""
    log_message("🔍 MONITORING STATUS CHECK")
    log_message("=" * 50)
    
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Test Telethon connection
    telethon_ok = await test_telethon_connection()
    
    if telethon_ok:
        status_message = f"""🔍 **Monitoring System Status Check**

**Timestamp:** {current_time}  
**VM:** sg-accident-monitor (us-central1-a)

**✅ Telethon Status:**
• Authentication: SUCCESS
• Session file: Valid  
• @sgaccident access: Confirmed
• Target channel access: Confirmed

**🔧 Action Required:**
• Monitoring needs to be restarted
• Session was restored successfully
• Ready for real-time monitoring

**Next Step:** Starting monitoring process..."""

        send_status_message(status_message)
        log_message("✅ System check completed - ready to start monitoring")
        return True
    else:
        status_message = f"""❌ **Monitoring System Issue**

**Timestamp:** {current_time}  
**VM:** sg-accident-monitor (us-central1-a)

**❌ Telethon Status:**
• Authentication: FAILED
• Session file: May be corrupted
• Channel access: Cannot verify

**🔧 Action Required:**
• Session file needs to be re-uploaded
• Manual restart required
• Check credentials and permissions"""

        send_status_message(status_message)
        log_message("❌ System check failed - manual intervention needed")
        return False

if __name__ == "__main__":
    asyncio.run(main())