#!/usr/bin/env python3
"""
Interactive Telethon session creation for @pukiboi
"""
import asyncio
import os
from telethon import TelegramClient

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"  # @pukiboi's phone number
SESSION_NAME = "pukiboi_working_session"

async def create_session():
    """Create and validate Telethon session interactively"""
    print(f"🔑 Creating Telethon session for {PHONE_NUMBER}")
    print("📱 Make sure you have access to receive SMS/calls for verification")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        print("🌐 Connecting to Telegram...")
        await client.connect()
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("✅ Already authorized!")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} (@{me.username})")
        else:
            print("🔐 Not authorized. Starting phone verification...")
            
            # Send code request
            await client.send_code_request(PHONE_NUMBER)
            print(f"📲 Verification code sent to {PHONE_NUMBER}")
            
            # Get verification code from user input
            code = input("Enter the verification code: ")
            
            try:
                await client.sign_in(PHONE_NUMBER, code)
                print("✅ Successfully signed in!")
                me = await client.get_me()
                print(f"👤 Logged in as: {me.first_name} (@{me.username})")
            except Exception as e:
                print(f"❌ Sign-in failed: {e}")
                print("💡 You may need 2FA password or try again")
                return False
        
        # Test channel access
        print("🔍 Testing @sgaccident channel access...")
        try:
            channel = await client.get_entity(-1001486947378)  # @sgaccident
            print(f"✅ Can access channel: {channel.title}")
            
            # Get recent messages to test
            messages = await client.get_messages(channel, limit=1)
            if messages:
                print(f"📄 Recent message preview: {messages[0].message[:50]}...")
            else:
                print("📄 No recent messages found")
                
        except Exception as e:
            print(f"❌ Cannot access @sgaccident channel: {e}")
            print("💡 Make sure @pukiboi has joined the @sgaccident channel")
            return False
        
        # Test target channel access  
        print("🔍 Testing target channel access...")
        try:
            target = await client.get_entity(-1003683261194)  # Target channel
            print(f"✅ Can access target: {target.title}")
        except Exception as e:
            print(f"⚠️  Cannot write to target channel: {e}")
            print("💡 Bot token may be needed for posting, but session is valid")
        
        print("🎉 Telethon session created successfully!")
        print(f"📁 Session file: {SESSION_NAME}.session")
        return True
        
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # Remove existing files to start fresh
    for ext in ["", ".session", ".session.backup"]:
        file_path = f"{SESSION_NAME}{ext}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Removed old file: {file_path}")
    
    success = asyncio.run(create_session())
    if success:
        print("\n✅ Ready to start Telethon monitoring!")
    else:
        print("\n❌ Session creation failed. Please try again.")