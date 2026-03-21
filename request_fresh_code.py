#!/usr/bin/env python3
"""
Request fresh verification code for Telethon
"""
import asyncio
import os
from telethon import TelegramClient

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_NAME = "pukiboi_final_session"

async def request_fresh_code():
    """Request a fresh verification code"""
    print(f"🔑 Requesting fresh verification code for {PHONE_NUMBER}")
    
    # Clean slate
    for ext in ["", ".session", ".session-journal"]:
        file_path = f"{SESSION_NAME}{ext}"
        if os.path.exists(file_path):
            os.remove(file_path)
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("🌐 Connecting to Telegram...")
        await client.connect()
        
        if await client.is_user_authorized():
            print("✅ Already authorized!")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} (@{me.username})")
            return True
        else:
            print("🔐 Requesting fresh verification code...")
            sent_code = await client.send_code_request(PHONE_NUMBER)
            print(f"✅ Fresh verification code sent to {PHONE_NUMBER}")
            print(f"📱 Code hash: {sent_code.phone_code_hash[:10]}...")
            print("")
            print("⏰ Please provide the NEW verification code you just received!")
            return False
            
    except Exception as e:
        print(f"❌ Code request failed: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(request_fresh_code())
    if not success:
        print("🔸 Waiting for fresh verification code...")