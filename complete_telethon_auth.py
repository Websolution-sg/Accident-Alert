#!/usr/bin/env python3
"""
Single-step Telethon session creation with proper state management
"""
import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_NAME = "pukiboi_working_session"
VERIFICATION_CODE = "53017"

async def complete_telethon_auth():
    """Complete Telethon authentication with verification code"""
    print(f"🔑 Setting up Telethon session for {PHONE_NUMBER}")
    print(f"📱 Using verification code: {VERIFICATION_CODE}")
    
    # Clean start - remove old session files
    for ext in ["", ".session", ".session-journal"]:
        file_path = f"{SESSION_NAME}{ext}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Removed old: {file_path}")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("🌐 Connecting to Telegram...")
        await client.connect()
        
        if await client.is_user_authorized():
            print("✅ Already authorized!")
        else:
            print("🔐 Starting fresh authentication...")
            
            # Send code request and immediately use it
            sent_code = await client.send_code_request(PHONE_NUMBER)
            print(f"📲 Code request sent (hash: {sent_code.phone_code_hash[:10]}...)")
            
            try:
                print(f"🔐 Signing in with code: {VERIFICATION_CODE}")
                await client.sign_in(PHONE_NUMBER, VERIFICATION_CODE, phone_code_hash=sent_code.phone_code_hash)
                print("✅ Successfully signed in!")
                
            except SessionPasswordNeededError:
                print("🔒 2FA password required")
                # For now, we'll handle this manually if needed
                raise Exception("2FA required - please handle manually")
        
        # Test authentication
        me = await client.get_me()
        print(f"👤 Authenticated as: {me.first_name} (@{me.username})")
        print(f"📱 Phone: {me.phone}")
        
        # Test @sgaccident channel access
        print("🔍 Testing @sgaccident channel access...")
        try:
            channel = await client.get_entity(-1001486947378)
            print(f"✅ Channel access: {channel.title}")
            
            # Get recent messages
            messages = await client.get_messages(channel, limit=3)
            print(f"📄 Found {len(messages)} recent messages")
            for i, msg in enumerate(messages[:2], 1):
                if msg.message:
                    print(f"   Message {i}: {msg.message[:60]}...")
                    
        except Exception as e:
            print(f"⚠️ Channel access issue: {e}")
            print("💡 Make sure @pukiboi has joined @sgaccident")
        
        # Test target channel access
        print("🔍 Testing target channel access...")
        try:
            target = await client.get_entity(-1003683261194)
            print(f"✅ Target channel: {target.title}")
        except Exception as e:
            print(f"⚠️ Target channel issue: {e}")
            print("💡 This might be normal - we'll use Bot API for posting")
        
        print(f"🎉 Telethon session successfully created!")
        print(f"📁 Session file: {SESSION_NAME}.session")
        print(f"💾 File size: {os.path.getsize(f'{SESSION_NAME}.session')} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(complete_telethon_auth())
    
    if success:
        print("\n✅ Ready for Telethon monitoring!")
        print("🚀 Next: Start the Telethon-based accident monitor")
    else:
        print("\n❌ Session setup failed")