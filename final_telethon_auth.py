#!/usr/bin/env python3
"""
Complete Telethon authentication with fresh verification code 15408
"""
import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_NAME = "pukiboi_final_session"
FRESH_CODE = "15408"

async def complete_authentication():
    """Complete authentication with fresh code"""
    print(f"🔑 Completing Telethon authentication for {PHONE_NUMBER}")
    print(f"📱 Using fresh verification code: {FRESH_CODE}")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("🌐 Connecting to Telegram...")
        await client.connect()
        
        if await client.is_user_authorized():
            print("✅ Already authorized!")
        else:
            print("🔐 Requesting code and signing in...")
            
            # Get fresh code request
            sent_code = await client.send_code_request(PHONE_NUMBER)
            print(f"📲 Using code hash: {sent_code.phone_code_hash[:10]}...")
            
            # Sign in with fresh code immediately
            try:
                await client.sign_in(PHONE_NUMBER, FRESH_CODE, phone_code_hash=sent_code.phone_code_hash)
                print("✅ Successfully authenticated!")
                
            except SessionPasswordNeededError:
                print("🔒 2FA password required")
                print("💡 Please check if 2FA is enabled on @pukiboi account")
                return False
        
        # Verify authentication
        me = await client.get_me()
        print(f"👤 Authenticated as: {me.first_name} (@{me.username})")
        print(f"📱 Phone: {me.phone}")
        print(f"🆔 User ID: {me.id}")
        
        # Test @sgaccident channel access
        print("\n🔍 Testing @sgaccident channel access...")
        try:
            channel = await client.get_entity(-1001486947378)
            print(f"✅ Channel access successful: {channel.title}")
            print(f"📊 Participants: {channel.participants_count}")
            
            # Get recent messages to test functionality
            messages = await client.get_messages(channel, limit=3)
            print(f"📄 Retrieved {len(messages)} recent messages:")
            for i, msg in enumerate(messages[:2], 1):
                if msg.message:
                    print(f"   {i}. {msg.message[:50]}...")
                    
        except Exception as e:
            print(f"❌ Channel access issue: {e}")
            print("💡 Ensure @pukiboi has joined @sgaccident channel")
            return False
        
        # Test target channel (for reference)
        print("\n🔍 Testing target channel access...")
        try:
            target = await client.get_entity(-1003683261194)
            print(f"✅ Target channel: {target.title}")
        except Exception as e:
            print(f"⚠️ Target channel issue: {e}")
            print("💡 This is normal - we'll use Bot API for posting")
        
        # Check session file
        session_file = f"{SESSION_NAME}.session"
        if os.path.exists(session_file):
            size = os.path.getsize(session_file)
            print(f"\n📁 Session file created: {session_file}")
            print(f"💾 File size: {size} bytes")
        
        print(f"\n🎉 Telethon session successfully created!")
        print(f"🔐 Authentication: @pukiboi user account")
        print(f"📺 Source: @sgaccident channel")
        print(f"✅ Ready for authentic user-based monitoring!")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        if "phone code entered was invalid" in str(e).lower():
            print("💡 The verification code was incorrect or expired")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(complete_authentication())
    
    if success:
        print("\n🚀 Telethon authentication complete!")
        print("📋 Next step: Start Telethon-based monitoring")
    else:
        print("\n❌ Authentication failed - please try again")