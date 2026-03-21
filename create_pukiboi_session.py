#!/usr/bin/env python3
"""
Create Telethon session for @pukiboi user account
Run this on YOUR LOCAL MACHINE (not the VM)
"""
import asyncio
from telethon import TelegramClient
import os

# @pukiboi credentials
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"  # @pukiboi's phone number

# Session file name
SESSION_FILE = "pukiboi_working_session"

# Test channel IDs
SGACCIDENT_CHANNEL_ID = -1001486947378  # @sgaccident (source)
TARGET_CHANNEL_ID = -1003683261194      # 🇸🇬Sg accidents (target)

async def create_session():
    """Create and validate Telethon session"""
    print("🔐 TELETHON SESSION CREATOR FOR @pukiboi")
    print("=" * 50)
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"💾 Session file: {SESSION_FILE}.session")
    print("=" * 50)
    
    # Remove existing session if present
    session_path = f"{SESSION_FILE}.session"
    if os.path.exists(session_path):
        os.remove(session_path)
        print(f"🗑️  Removed existing session file")
    
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        print("📞 Connecting to Telegram...")
        await client.start(phone=PHONE_NUMBER)
        
        # Get user info
        me = await client.get_me()
        print(f"✅ Authenticated as: @{me.username} ({me.first_name})")
        
        # Test channel access
        print("\n🔍 Testing channel access...")
        
        try:
            sgaccident = await client.get_entity(SGACCIDENT_CHANNEL_ID)
            print(f"✅ Source channel: {sgaccident.title} (ID: {SGACCIDENT_CHANNEL_ID})")
        except Exception as e:
            print(f"❌ Cannot access source channel {SGACCIDENT_CHANNEL_ID}: {e}")
            return False
            
        try:
            target = await client.get_entity(TARGET_CHANNEL_ID)
            print(f"✅ Target channel: {target.title} (ID: {TARGET_CHANNEL_ID})")
        except Exception as e:
            print(f"❌ Cannot access target channel {TARGET_CHANNEL_ID}: {e}")
            return False
        
        print("\n🎉 SUCCESS! Session created and validated!")
        print(f"📄 Session file created: {session_path}")
        print("\n📎 Next steps:")
        print("1. Upload this session file to the VM")
        print("2. Start Telethon monitoring on the VM")
        
        return True
        
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Make sure you have access to @pukiboi's Telegram account!")
    print("⚠️  You'll need to enter the verification code that Telegram sends.\n")
    
    input("Press ENTER when ready to start session creation...")
    
    try:
        success = asyncio.run(create_session())
        if success:
            print("\n✅ Ready to deploy to VM!")
        else:
            print("\n❌ Session creation failed. Check your credentials and permissions.")
    except KeyboardInterrupt:
        print("\n🛑 Session creation cancelled by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")