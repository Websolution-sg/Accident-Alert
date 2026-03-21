#!/usr/bin/env python3
"""
LOCAL Telethon Session Creator for @pukiboi
Run this on your LOCAL machine to create a working session file
Then upload the session file to your VM
"""
import asyncio
import os
from telethon import TelegramClient

# API Configuration for @pukiboi
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_FILE = "pukiboi_working_session"

async def create_working_session():
    """Create a working Telethon session locally"""
    print("🔧 Creating Telethon session for @pukiboi")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print("📝 You'll need to enter the verification code from Telegram")
    print()
    
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        # Start client with phone number
        print("📞 Starting authentication...")
        await client.start(phone=PHONE_NUMBER)
        
        # Get user info
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: @{me.username} ({me.first_name})")
        
        # Test channel access
        try:
            sgaccident = await client.get_entity(-1001486947378)
            target = await client.get_entity(-1003683261194)
            print(f"✅ Source channel access: {sgaccident.title}")
            print(f"✅ Target channel access: {target.title}")
        except Exception as e:
            print(f"⚠️  Channel access test: {e}")
        
        print("\n✅ Session created successfully!")
        print(f"📁 Session file: {SESSION_FILE}.session")
        print()
        print("📤 Next steps:")
        print("1. Upload this session file to your VM:")
        print(f"   gcloud compute scp {SESSION_FILE}.session user@sg-accident-monitor:/tmp/pukiboi_session.session --zone=us-central1-a --project=verdant-petal-485213-h2")
        print("2. The VM monitoring will automatically use this session")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🚀 TELETHON SESSION CREATOR")
    print("=" * 40)
    print("⚠️  Run this on your LOCAL machine (not VM)")
    print("=" * 40)
    print()
    
    try:
        result = asyncio.run(create_working_session())
        if result:
            print("\n🎉 Success! Ready to upload to VM.")
        else:
            print("\n❌ Failed to create session.")
    except KeyboardInterrupt:
        print("\n🛑 Cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")