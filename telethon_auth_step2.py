#!/usr/bin/env python3
"""
Two-step Telethon session creation for @pukiboi
Step 1: Request verification code
Step 2: Complete authentication with code
"""
import asyncio
import os
import sys
from telethon import TelegramClient

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SESSION_NAME = "pukiboi_working_session"

async def request_code():
    """Step 1: Request verification code"""
    print(f"🔑 Requesting verification code for {PHONE_NUMBER}")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            print("✅ Already authorized!")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} (@{me.username})")
            return True
        else:
            print("🔐 Sending verification code...")
            await client.send_code_request(PHONE_NUMBER)
            print(f"✅ Verification code sent to {PHONE_NUMBER}")
            print("📱 Check your phone for SMS!")
            print("")
            print("🔸 Next step: Run this command with your code:")
            print(f"   python3 telethon_auth_step2.py YOUR_CODE_HERE")
            return False
            
    except Exception as e:
        print(f"❌ Code request failed: {e}")
        return False
        
    finally:
        await client.disconnect()

async def complete_auth(code):
    """Step 2: Complete authentication with verification code"""
    print(f"🔐 Completing authentication with code: {code}")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            print("✅ Already authorized!")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} (@{me.username})")
        else:
            print("🔐 Signing in with verification code...")
            await client.sign_in(PHONE_NUMBER, code)
            print("✅ Successfully signed in!")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} (@{me.username})")
        
        # Test channel access
        print("🔍 Testing @sgaccident channel access...")
        try:
            channel = await client.get_entity(-1001486947378)
            print(f"✅ Can access channel: {channel.title}")
            
            messages = await client.get_messages(channel, limit=1)
            if messages:
                print(f"📄 Recent message: {messages[0].message[:50]}...")
                
        except Exception as e:
            print(f"❌ Channel access issue: {e}")
            return False
        
        print("🎉 Telethon session created successfully!")
        print(f"📁 Session file: {SESSION_NAME}.session")
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        if "phone code entered was invalid" in str(e):
            print("💡 The verification code was incorrect. Please check and try again.")
        elif "Two-steps verification is enabled" in str(e):
            print("💡 2FA is enabled. You need the 2FA password.")
            password = input("Enter your 2FA password: ")
            try:
                await client.sign_in(password=password)
                print("✅ 2FA authentication successful!")
                return True
            except Exception as e2:
                print(f"❌ 2FA failed: {e2}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Step 2: Complete with verification code
        code = sys.argv[1]
        success = asyncio.run(complete_auth(code))
    else:
        # Step 1: Request verification code
        success = asyncio.run(request_code())
        
    if success:
        print("\n✅ Authentication complete!")
    else:
        print("\n❌ Authentication failed.")