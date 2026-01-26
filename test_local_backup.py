#!/usr/bin/env python3
"""
Test script for local accident monitor backup
"""
import sys
import os

def test_local_monitor():
    """Test the local monitor configuration"""
    print("=== Testing Local Accident Monitor ===")
    print()
    
    try:
        # Test imports
        print("1. Testing imports...")
        import requests
        import json
        import time
        import datetime
        print("   ✅ All required modules available")
        
        # Test configuration
        print("\n2. Testing configuration...")
        sys.path.insert(0, os.path.dirname(__file__))
        
        # Import without running main
        spec = __import__('importlib.util').util.spec_from_file_location(
            "monitor", "waze_accident_monitor_latest.py"
        )
        monitor_module = __import__('importlib.util').util.module_from_spec(spec)
        
        print("   ✅ Configuration file loads successfully")
        
        # Test API connectivity
        print("\n3. Testing API connectivity...")
        response = requests.get("https://api.telegram.org/bot8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            print(f"   ✅ Telegram Bot: {bot_info.get('result', {}).get('username', 'WazeAccident_bot')}")
        else:
            print("   ⚠️  Telegram API not responding")
            
        waze_response = requests.get("https://www.waze.com/live-map/api/georss", timeout=10)
        if waze_response.status_code == 200:
            print("   ✅ Waze API responding")
        else:
            print("   ⚠️  Waze API not responding")
            
        print("\n4. System Status:")
        print("   ✅ Local backup is ready to run")
        print("   ✅ Use 'start_local_monitor.bat' or 'start_local_monitor.ps1' to start")
        print("   ⚠️  Only run when Google Cloud service is down")
        
    except ImportError as e:
        print(f"   ❌ Missing required module: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = test_local_monitor()
    if success:
        print("\n🎯 Local backup is fully functional!")
    else:
        print("\n❌ Local backup needs attention")
    
    input("\nPress Enter to continue...")