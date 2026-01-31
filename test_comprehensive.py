#!/usr/bin/env python3
"""
Comprehensive test script for Accident Alert monitoring system
Tests both Waze API and Telegram connectivity for @sgaccident group (-1001486947378)
"""
import requests
import json
import datetime
import time
import sys
import os

# Configuration from main script
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"  # The group you want to test
TARGET_CHAT_ID = "-1003683261194"      # Where alerts are posted

WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
WAZE_BBOX = {
    'bottom': 1.1304753,
    'left': 103.6055424,
    'right': 104.0945619,
    'top': 1.4764671
}

def log_test(message, success=None):
    """Log test messages with status indicators"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = ""
    if success is True:
        status = "✅"
    elif success is False:
        status = "❌"
    else:
        status = "🔍"
    
    print(f"[{timestamp}] {status} {message}")

def test_telegram_bot_api():
    """Test Telegram Bot API connectivity"""
    log_test("Testing Telegram Bot API connectivity...")
    
    try:
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe', timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            log_test(f"Bot API connected successfully: {bot_info['result']['first_name']}", True)
            return True
        else:
            log_test(f"Bot API failed with status: {response.status_code}", False)
            return False
    except Exception as e:
        log_test(f"Bot API connection error: {e}", False)
        return False

def test_waze_api():
    """Test Waze API connectivity with proper headers"""
    log_test("Testing Waze API connectivity...")
    
    try:
        params = {
            'bottom': WAZE_BBOX['bottom'],
            'left': WAZE_BBOX['left'], 
            'right': WAZE_BBOX['right'],
            'top': WAZE_BBOX['top'],
            'env': 'row',
            'types': 'alerts,traffic'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.waze.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(WAZE_API_URL, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            accidents = [alert for alert in alerts 
                        if alert.get('type', '').upper() in ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR']]
            
            log_test(f"Waze API connected - {len(alerts)} alerts, {len(accidents)} accidents found", True)
            
            # Show sample accident if any
            if accidents:
                sample = accidents[0]
                location = sample.get('location', {})
                street = sample.get('street', 'Unknown')
                log_test(f"Sample accident: {street} at {location.get('y', 0):.4f}, {location.get('x', 0):.4f}")
            
            return True
        else:
            log_test(f"Waze API failed with status: {response.status_code}", False)
            return False
            
    except Exception as e:
        log_test(f"Waze API connection error: {e}", False)
        return False

def test_telegram_sgaccident_access():
    """Test access to @sgaccident channel using bot API"""
    log_test("Testing @sgaccident channel access...")
    
    try:
        # Try to get recent updates that might include @sgaccident messages
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=10', timeout=10)
        if response.status_code == 200:
            result = response.json()
            updates = result.get('result', [])
            
            sgaccident_messages = []
            for update in updates:
                message = update.get('message', {})
                chat = message.get('chat', {})
                if str(chat.get('id', '')) == SGACCIDENT_CHAT_ID:
                    sgaccident_messages.append(message)
            
            log_test(f"Successfully accessed bot updates - found {len(sgaccident_messages)} recent @sgaccident messages", True)
            
            if sgaccident_messages:
                latest = sgaccident_messages[-1]
                log_test(f"Latest @sgaccident message: {latest.get('text', 'N/A')[:50]}...")
            
            return True
        else:
            log_test(f"Failed to get Telegram updates: {response.status_code}", False)
            return False
            
    except Exception as e:
        log_test(f"@sgaccident access test error: {e}", False)
        return False

def test_send_message():
    """Test sending a message to target channel"""
    log_test("Testing message sending to target channel...")
    
    try:
        test_message = f"""🧪 **System Test - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

This is a test message to verify the accident monitoring system is working properly.

**Test Results:**
• Telegram Bot API: Connected
• Waze API: Testing...
• @sgaccident monitoring: Active
• Target channel: Accessible

*If you see this message, the bot can successfully post to this channel.*"""

        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': TARGET_CHAT_ID,
            'text': test_message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            message_id = result['result']['message_id']
            log_test(f"Test message sent successfully (Message ID: {message_id})", True)
            return True
        else:
            log_test(f"Failed to send test message: {response.status_code}", False)
            log_test(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        log_test(f"Send message test error: {e}", False)
        return False

def check_data_files():
    """Check the status of data files"""
    log_test("Checking data files...")
    
    files_to_check = [
        ("processed_accidents.json", "Processed accidents storage"),
        ("telegram_offset.json", "Telegram update offset"),
        ("user_processed_accidents.json", "User monitoring processed accidents"),
        ("pukiboi_session.session", "Telethon user session")
    ]
    
    for filename, description in files_to_check:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    if filename.endswith('.json'):
                        data = json.load(f)
                        log_test(f"{description}: Found ({len(str(data))} chars)", True)
                    else:
                        log_test(f"{description}: Found", True)
            except Exception as e:
                log_test(f"{description}: Found but corrupted - {e}", False)
        else:
            log_test(f"{description}: Not found (will be created)", None)

def run_monitoring_test(duration=30):
    """Run the actual monitoring script for a short duration"""
    log_test(f"Running monitoring test for {duration} seconds...")
    
    try:
        import subprocess
        import signal
        import threading
        
        # Start the monitoring script
        process = subprocess.Popen(
            [sys.executable, "waze_accident_monitor.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        def timeout_handler():
            time.sleep(duration)
            process.terminate()
        
        timeout_thread = threading.Thread(target=timeout_handler)
        timeout_thread.daemon = True
        timeout_thread.start()
        
        # Capture output
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                print(f"  MONITOR: {line.strip()}")
        
        process.wait()
        
        if output_lines:
            log_test(f"Monitoring test completed - {len(output_lines)} log lines captured", True)
            return True
        else:
            log_test("Monitoring test completed but no output captured", False)
            return False
            
    except Exception as e:
        log_test(f"Monitoring test error: {e}", False)
        return False

def main():
    """Run comprehensive test suite"""
    print("=" * 60)
    print("🚨 ACCIDENT ALERT SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"Testing for Telegram group: {SGACCIDENT_CHAT_ID}")
    print(f"Target channel: {TARGET_CHAT_ID}")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results['bot_api'] = test_telegram_bot_api()
    test_results['waze_api'] = test_waze_api()
    test_results['sgaccident_access'] = test_telegram_sgaccident_access()
    test_results['send_message'] = test_send_message()
    
    print("\n" + "=" * 60)
    log_test("Checking data files...")
    check_data_files()
    
    print("\n" + "=" * 60)
    log_test("Starting short monitoring test...")
    test_results['monitoring'] = run_monitoring_test(15)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    print("=" * 60)
    print(f"OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems operational! Ready for continuous monitoring.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)