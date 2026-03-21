#!/usr/bin/env python3
"""
Telethon Session Validator - Check if session works without interactive auth
"""
import asyncio
import sys
from telethon import TelegramClient

# API Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
SESSION_FILE = "pukiboi_session"

async def test_session():
    """Test if session works without authentication"""
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        # Connect without starting authentication flow
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Session is valid! Logged in as: @{me.username} ({me.first_name})")
            
            # Test channel access
            try:
                sgaccident = await client.get_entity(-1001486947378)
                target = await client.get_entity(-1003683261194) 
                print(f"✅ Can access source: {sgaccident.title}")
                print(f"✅ Can access target: {target.title}")
                print("🚀 Ready for Telethon monitoring!")
                return True
            except Exception as e:
                print(f"⚠️  Channel access limited: {e}")
                return True  # Session is still valid
                
        else:
            print("❌ Session expired or invalid - needs re-authentication")
            return False
            
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_session())
    sys.exit(0 if result else 1)