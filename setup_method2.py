#!/usr/bin/env python3
"""
Test and setup script for Method 2 - User-based @sgaccident monitoring
"""
import asyncio
import sys
import datetime
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Configuration from user_sgaccident_monitor.py
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"
SGACCIDENT_CHANNEL_ID = -1001486947378
TARGET_CHANNEL_ID = -1003683261194
SESSION_FILE = "pukiboi_session"

async def test_user_account_setup():
    """Test user account setup and channel access"""
    print("🔧 METHOD 2 SETUP - USER-BASED MONITORING")
    print("=" * 60)
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"🎯 Monitoring: @sgaccident ({SGACCIDENT_CHANNEL_ID})")
    print(f"📤 Target: {TARGET_CHANNEL_ID}")
    print("=" * 60)
    
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        print("🔐 Connecting to Telegram...")
        await client.start()
        
        # Check if we're logged in
        me = await client.get_me()
        print(f"✅ Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no_username'})")
        print(f"📞 Phone: {me.phone}")
        
        # Test access to @sgaccident channel
        print(f"\n🔍 Testing access to @sgaccident channel...")
        try:
            sgaccident_entity = await client.get_entity(SGACCIDENT_CHANNEL_ID)
            print(f"✅ @sgaccident access: {sgaccident_entity.title}")
            print(f"   Type: {type(sgaccident_entity).__name__}")
            print(f"   Participants: {getattr(sgaccident_entity, 'participants_count', 'Unknown')}")
        except Exception as e:
            print(f"❌ Cannot access @sgaccident: {e}")
            return False
        
        # Test access to target channel
        print(f"\n🔍 Testing access to target channel...")
        try:
            target_entity = await client.get_entity(TARGET_CHANNEL_ID)
            print(f"✅ Target channel access: {target_entity.title}")
            print(f"   Type: {type(target_entity).__name__}")
        except Exception as e:
            print(f"❌ Cannot access target channel: {e}")
            return False
        
        # Test sending a message
        print(f"\n📤 Testing message sending...")
        test_message = f"""🧪 **Method 2 Test - {datetime.datetime.now().strftime('%H:%M:%S')}**

User-based @sgaccident monitoring test successful!

**Method 2 Advantages:**
⚡ Real-time notifications (0-1 second delay)
🔓 Better channel access than bots
📱 Uses @pukiboi user account

**Status:** Ready to monitor @sgaccident with improved filters!"""
        
        try:
            sent_msg = await client.send_message(TARGET_CHANNEL_ID, test_message)
            print(f"✅ Test message sent successfully (ID: {sent_msg.id})")
        except Exception as e:
            print(f"❌ Failed to send test message: {e}")
            return False
        
        # Get recent messages from @sgaccident to test filtering
        print(f"\n📋 Testing message retrieval from @sgaccident...")
        try:
            messages = await client.get_messages(SGACCIDENT_CHANNEL_ID, limit=5)
            print(f"✅ Retrieved {len(messages)} recent messages")
            
            for i, msg in enumerate(messages, 1):
                if msg.text:
                    print(f"   {i}. [{msg.date.strftime('%H:%M')}] {msg.text[:60]}{'...' if len(msg.text) > 60 else ''}")
                else:
                    print(f"   {i}. [{msg.date.strftime('%H:%M')}] (No text content)")
                    
        except Exception as e:
            print(f"❌ Cannot retrieve messages from @sgaccident: {e}")
            return False
        
        print(f"\n🎉 METHOD 2 SETUP COMPLETE!")
        print("=" * 60)
        print("✅ All tests passed - ready for real-time monitoring")
        print("📱 User account has full access to @sgaccident")
        print("⚡ Will receive instant notifications (vs 60s polling)")
        print("🚀 Run 'python user_sgaccident_monitor.py' to start monitoring")
        
        return True
        
    except SessionPasswordNeededError:
        print("🔐 Two-factor authentication detected")
        password = input("Enter your 2FA password: ")
        await client.sign_in(password=password)
        return await test_user_account_setup()  # Retry after 2FA
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
        
    finally:
        await client.disconnect()

async def main():
    """Main setup function"""
    success = await test_user_account_setup()
    
    if success:
        print(f"\n💡 NEXT STEPS:")
        print("1. Stop Method 1 (bot API) monitoring on your VM if desired")
        print("2. Run Method 2: python user_sgaccident_monitor.py")
        print("3. Or run both methods simultaneously for redundancy")
    else:
        print(f"\n⚠️  Setup incomplete - check the errors above")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\\n⏹️  Setup cancelled by user")
        sys.exit(1)