#!/usr/bin/env python3
"""
True Telethon Authentication Setup for @pukiboi
Creates a working session for background monitoring
"""
import asyncio
import os
from telethon import TelegramClient

# API Configuration for @pukiboi
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_FILE = "pukiboi_session"

async def setup_telethon_session():
    """Set up Telethon session for background use"""
    print(f"🔧 Setting up Telethon session for @pukiboi ({PHONE_NUMBER})")
    
    # Create client
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        # Start client - this will handle authentication
        await client.start(phone=PHONE_NUMBER)
        
        # Test connection
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: @{me.username} ({me.first_name})")
        
        # Test channel access
        try:
            sgaccident = await client.get_entity(-1001486947378)
            target = await client.get_entity(-1003683261194)
            print(f"✅ Source channel access: {sgaccident.title}")
            print(f"✅ Target channel access: {target.title}")
        except Exception as e:
            print(f"⚠️  Channel access test failed: {e}")
        
        print("✅ Session setup complete! Ready for background monitoring.")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    finally:
        await client.disconnect()
    
    return True

if __name__ == "__main__":
    result = asyncio.run(setup_telethon_session())
    if result:
        print("\n🚀 Session is ready. You can now start background monitoring.")
    else:
        print("\n❌ Session setup failed. Check credentials and try again.")