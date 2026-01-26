#!/usr/bin/env python3
import requests
import json
import datetime

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"  # @sgaccident channel
TARGET_CHAT_ID = "-1003683261194"      # Your target channel

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_bot_permissions():
    """Test bot access to both channels"""
    log_message("Testing bot permissions...")
    
    # Test source channel access
    log_message("Testing @sgaccident channel access...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        response = requests.get(url, params={'chat_id': SGACCIDENT_CHAT_ID}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat_info = data.get('result', {})
                title = chat_info.get('title', 'Unknown')
                log_message(f"✅ Source channel access OK: {title}")
            else:
                log_message(f"❌ Source channel error: {data.get('description', 'Unknown')}")
        else:
            log_message(f"❌ Source channel HTTP error: {response.status_code}")
    except Exception as e:
        log_message(f"❌ Source channel test failed: {e}")
    
    # Test target channel access
    log_message("Testing target channel access...")
    try:
        test_message = "🔧 Bot test - checking permissions"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TARGET_CHAT_ID,
            "text": test_message
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                log_message("✅ Target channel access OK - test message sent")
                
                # Delete the test message
                message_id = data.get('result', {}).get('message_id')
                if message_id:
                    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
                    delete_payload = {"chat_id": TARGET_CHAT_ID, "message_id": message_id}
                    requests.post(delete_url, json=delete_payload)
                    log_message("🧹 Test message deleted")
            else:
                log_message(f"❌ Target channel error: {data.get('description', 'Unknown')}")
        else:
            log_message(f"❌ Target channel HTTP error: {response.status_code}")
    except Exception as e:
        log_message(f"❌ Target channel test failed: {e}")

def explain_limitation():
    """Explain the historical message limitation"""
    print("\n" + "="*70)
    print("📋 HISTORICAL MESSAGE EXTRACTION - IMPORTANT LIMITATION")
    print("="*70)
    print()
    print("❌ ISSUE: Telegram Bot API cannot access historical channel messages")
    print("   - getUpdates only shows messages sent AFTER bot started listening")
    print("   - No API method exists to retrieve past channel messages")
    print("   - This is a Telegram security/privacy limitation")
    print()
    print("✅ SOLUTION: Start monitoring system to catch NEW accidents")
    print("   - Run: python waze_accident_monitor.py")
    print("   - Bot will forward NEW @sgaccident posts to your channel")
    print("   - All future accidents will be automatically reposted")
    print()
    print("🔍 ALTERNATIVES for historical data:")
    print("   1. Manual copy-paste from @sgaccident web interface")
    print("   2. Use Telegram Desktop export feature")
    print("   3. Wait for new accidents to be auto-forwarded")
    print()
    print("💡 RECOMMENDATION:")
    print("   Start the monitoring system now to catch all future accidents!")
    print("="*70)

def main():
    """Main function to test and explain"""
    log_message("🔍 Checking accident extraction capabilities...")
    print()
    
    # Test bot permissions
    test_bot_permissions()
    print()
    
    # Explain limitation
    explain_limitation()
    print()
    
    log_message("✅ Permission check complete!")
    log_message("💡 To start monitoring NEW accidents, run: python waze_accident_monitor.py")

if __name__ == "__main__":
    main()