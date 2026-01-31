#!/usr/bin/env python3
"""
Verify monitoring location - Google VM vs Local PC
"""
import asyncio
import requests
import datetime
import sys
from telethon import TelegramClient

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHAT_ID = "-1003683261194"
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
SESSION_FILE = "pukiboi_session"

async def test_telethon_conflict():
    """Test if Telethon user account is already in use (VM conflict)"""
    print("🔍 Testing Telethon user account availability...")
    
    try:
        client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        await client.start()
        
        # Try to get account info
        me = await client.get_me()
        print(f"✅ Local Telethon access: Available")
        print(f"   Account: {me.first_name} (@{me.username or 'no_username'})")
        
        await client.disconnect()
        return False  # No conflict, VM not using it
        
    except Exception as e:
        error_str = str(e).lower()
        if 'already' in error_str or 'another' in error_str or 'session' in error_str:
            print(f"⚡ Local Telethon access: BLOCKED - VM is using the session!")
            return True  # Conflict detected, VM is running
        else:
            print(f"❌ Telethon error: {e}")
            return None  # Unknown error

def test_bot_api_conflict():
    """Test if Bot API has conflicts (indicates VM bot is running)"""
    print("🔍 Testing Bot API availability...")
    
    try:
        # Try to get updates with timeout - if VM is polling, we'll get 409
        response = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=5&limit=1',
            timeout=10
        )
        
        if response.status_code == 409:
            print("⚡ Bot API conflict: VM bot is ACTIVE (409 detected)")
            return True
        elif response.status_code == 200:
            print("✅ Bot API available: No VM bot detected")
            return False
        else:
            print(f"❓ Bot API unexpected response: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Bot API test error: {e}")
        return None

def send_location_check_message():
    """Send message to identify monitoring source"""
    print("📤 Sending location verification message...")
    
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    message = f"""🔍 **Monitoring Location Check - {current_time}**

**Testing monitoring source:**
• If you see this message, the bot can post
• Checking where @sgaccident monitoring is running from
• Method 2 deployment status verification

**Expected:** Google VM running Method 2 (user-based)
**Current time:** {current_time} (Local PC time)

*Monitoring source will be confirmed based on session conflicts...*"""

    try:
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={
                'chat_id': TARGET_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            msg_id = result['result']['message_id']
            print(f"✅ Location check message sent (ID: {msg_id})")
            return msg_id
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Message sending error: {e}")
        return None

async def main():
    """Main verification function"""
    print("🏠🆚☁️  MONITORING LOCATION VERIFICATION")
    print("=" * 60)
    print("Checking if monitoring is running from Google VM or Local PC...")
    print()
    
    # Test 1: Check Bot API conflicts
    bot_conflict = test_bot_api_conflict()
    print()
    
    # Test 2: Check Telethon user account conflicts
    telethon_conflict = await test_telethon_conflict()
    print()
    
    # Test 3: Send verification message
    msg_id = send_location_check_message()
    print()
    
    # Analyze results
    print("=" * 60)
    print("📊 VERIFICATION RESULTS:")
    print("=" * 60)
    
    vm_indicators = 0
    local_indicators = 0
    
    if bot_conflict is True:
        print("🔍 Bot API: VM conflict detected (VM bot active)")
        vm_indicators += 1
    elif bot_conflict is False:
        print("🔍 Bot API: No conflict (VM bot inactive)")
        local_indicators += 1
    else:
        print("🔍 Bot API: Status unclear")
    
    if telethon_conflict is True:
        print("🔍 Telethon: VM session conflict (VM using @pukiboi account)")
        vm_indicators += 1
    elif telethon_conflict is False:
        print("🔍 Telethon: No conflict (VM not using account)")
        local_indicators += 1
    else:
        print("🔍 Telethon: Status unclear")
    
    print("=" * 60)
    
    if vm_indicators >= 1 and local_indicators == 0:
        print("🎯 CONCLUSION: Monitoring is running from GOOGLE VM ✅")
        print("   • VM has taken control of monitoring resources")
        print("   • Method 2 is active on VM infrastructure") 
        print("   • Local PC is not running monitoring")
        
    elif local_indicators >= 1 and vm_indicators == 0:
        print("🎯 CONCLUSION: Monitoring is running from LOCAL PC ⚠️")
        print("   • VM deployment may not have completed")
        print("   • Check VM status and deployment logs")
        print("   • Consider redeploying to VM")
        
    elif vm_indicators >= 1 and local_indicators >= 1:
        print("🎯 CONCLUSION: BOTH VM and LOCAL PC may be running ⚠️")
        print("   • This could cause conflicts or duplicates")
        print("   • Stop local monitoring if VM is intended")
        
    else:
        print("🎯 CONCLUSION: Status unclear - check manually")
        print("   • Check VM logs and service status")
        print("   • Verify deployment completed successfully")
    
    print("=" * 60)
    
    if vm_indicators >= 1:
        print("🎉 SUCCESS: Google VM monitoring is operational!")
        return True
    else:
        print("⚠️  VM monitoring status needs verification")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\\n⏹️  Verification cancelled")
        sys.exit(1)