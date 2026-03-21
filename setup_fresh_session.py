#!/usr/bin/env python3
"""
Create a fresh Telethon session for @pukiboi account
"""
import asyncio
from telethon import TelegramClient

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_FILE = "pukiboi_session_fresh"

async def create_session():
    """Create fresh session"""
    print("🔧 Creating fresh Telethon session...")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"📁 Session: {SESSION_FILE}")
    print("=" * 50)
    
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        
        # Test the connection
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name} (@{me.username})")
        
        # Test channel access
        sgaccident_entity = await client.get_entity(-1001486947378)
        target_entity = await client.get_entity(-1003683261194)
        
        print(f"✅ Source channel access: {sgaccident_entity.title}")
        print(f"✅ Target channel access: {target_entity.title}")
        
        print("=" * 50)
        print("🎉 Fresh session created successfully!")
        print(f"📁 Session file: {SESSION_FILE}.session")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(create_session())