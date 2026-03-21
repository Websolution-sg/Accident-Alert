#!/usr/bin/env python3
"""
Simple test script to verify Telethon session on VM
"""
import asyncio
import sys
from telethon import TelegramClient

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
SESSION_FILE = "pukiboi_session"
SGACCIDENT_CHANNEL_ID = -1001486947378
TARGET_CHANNEL_ID = -1003683261194

async def test_connection():
    print("🔧 Testing Telethon connection...")
    
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        await client.start()
        
        # Test authentication
        me = await client.get_me()
        print(f"✅ Authenticated as: {me.first_name} (@{me.username})")
        
        # Test channel access
        try:
            sgaccident = await client.get_entity(SGACCIDENT_CHANNEL_ID)
            print(f"✅ Source channel: {sgaccident.title}")
            
            target = await client.get_entity(TARGET_CHANNEL_ID)  
            print(f"✅ Target channel: {target.title}")
            
            # Test getting recent messages
            messages = await client.get_messages(SGACCIDENT_CHANNEL_ID, limit=3)
            print(f"✅ Retrieved {len(messages)} recent messages")
            
            print("🎉 All tests passed - session is working!")
            return True
            
        except Exception as e:
            print(f"❌ Channel access error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)