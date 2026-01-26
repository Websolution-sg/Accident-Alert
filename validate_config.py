#!/usr/bin/env python3
"""
Validate that the code is correctly configured for the specified channel and bot
"""
import os
import sys

def validate_configuration():
    """Validate the configuration in waze_accident_monitor.py"""
    
    expected_bot_token = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
    expected_channel_id = "-1003683261194"
    expected_channel_url = "https://web.telegram.org/a/#-1003683261194"
    
    print("🔍 CONFIGURATION VALIDATION")
    print("=" * 40)
    
    # Read the main monitoring script
    try:
        with open('waze_accident_monitor.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ waze_accident_monitor.py not found!")
        return False
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open('waze_accident_monitor.py', 'r', encoding='latin1') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Could not read file: {e}")
            return False
    
    validation_passed = True
    
    # Check 1: Bot token in main function
    if expected_bot_token in content:
        print("✅ Correct bot token found in code")
    else:
        print("❌ Expected bot token NOT found in code")
        validation_passed = False
    
    # Check 2: Channel ID in main function
    if expected_channel_id in content:
        print("✅ Correct channel ID found in code")
    else:
        print("❌ Expected channel ID NOT found in code")
        validation_passed = False
    
    # Check 3: No old bot token references
    old_bot_token = "REMOVED_OLD_BOT_TOKEN"
    if old_bot_token not in content:
        print("✅ Old bot token NOT found (good)")
    else:
        print("❌ Old bot token still referenced in code")
        validation_passed = False
    
    # Check 4: No old channel ID references
    old_channel_id = "REMOVED_OLD_CHANNEL_ID"
    if old_channel_id not in content:
        print("✅ Old channel ID NOT found (good)")
    else:
        print("❌ Old channel ID still referenced in code")
        validation_passed = False
    
    # Check 5: send_telegram_message function is active (not disabled)
    if "POSTING DISABLED" not in content:
        print("✅ Posting function is ACTIVE")
    else:
        print("❌ Posting function is DISABLED")
        validation_passed = False
    
    print("\n📊 CONFIGURATION DETAILS:")
    print(f"🎯 Target Channel: {expected_channel_url}")
    print(f"🤖 Bot Token: {expected_bot_token[:20]}...")
    print(f"📱 Channel ID: {expected_channel_id}")
    
    # Test import
    print("\n🧪 IMPORT TEST:")
    try:
        # Import and create instance to validate
        sys.path.insert(0, '.')
        from waze_accident_monitor import WazeAccidentMonitor
        
        # Create test instance
        monitor = WazeAccidentMonitor(expected_bot_token, expected_channel_id)
        
        # Check if instance has correct values
        if monitor.telegram_bot_token == expected_bot_token:
            print("✅ Bot token correctly loaded in class")
        else:
            print("❌ Bot token mismatch in class")
            validation_passed = False
            
        if monitor.telegram_channel_id == expected_channel_id:
            print("✅ Channel ID correctly loaded in class")
        else:
            print("❌ Channel ID mismatch in class")
            validation_passed = False
            
        print("✅ Script imports and initializes correctly")
        
    except Exception as e:
        print(f"❌ Import/initialization error: {e}")
        validation_passed = False
    
    print("\n" + "=" * 40)
    if validation_passed:
        print("🎉 VALIDATION PASSED!")
        print("✅ Code is correctly configured for:")
        print(f"   Channel: {expected_channel_url}")
        print(f"   Bot: @WazeAccident_bot")
        return True
    else:
        print("❌ VALIDATION FAILED!")
        print("⚠️  Code has configuration issues that need fixing")
        return False

if __name__ == "__main__":
    validate_configuration()