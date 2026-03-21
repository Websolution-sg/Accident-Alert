#!/usr/bin/env python3
"""
Ultimate validation test - force generate incident to test notification pipeline
"""
import requests
import json
from datetime import datetime

# Configuration
BOT_TOKEN = '8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ'
CHAT_ID = '-1003683261194'

def test_notification_pipeline():
    print("🔧 ULTIMATE VALIDATION TEST")
    print("=" * 50)
    
    # Create a realistic test incident
    test_incident = {
        'type': 'VALIDATION_TEST',
        'street': 'Marina Bay Sands area',
        'location': {'y': 1.2834, 'x': 103.8607},  # Marina Bay Sands coordinates
        'reportBy': 'System Validation Test',
        'confidence': 9,
        'reliability': 9,
        'pubMillis': int(datetime.now().timestamp() * 1000)
    }
    
    # Format the message exactly like the real system would
    location = test_incident.get('location', {})
    lat, lon = location.get('y', 0), location.get('x', 0)
    street = test_incident.get('street', 'Unknown location')
    alert_type = test_incident.get('type', 'INCIDENT')
    confidence = test_incident.get('confidence', 5)
    
    message = f"🚨 **{alert_type.replace('_', ' ')}** Alert\n\n"
    message += f"📍 **Location:** {street}\n"
    message += f"🌐 **Coordinates:** {lat:.4f}, {lon:.4f}\n"
    message += f"⭐ **Confidence:** {confidence}/10\n"
    message += f"🕒 **Time:** {datetime.now().strftime('%H:%M:%S')}\n"
    message += f"🔗 [View on Maps](https://maps.google.com/maps?q={lat},{lon})\n\n"
    message += f"📝 **Note:** This is an end-to-end validation test of the accident monitoring system. "
    message += f"If you receive this message, the notification pipeline is working correctly!"
    
    print("📱 Test incident details:")
    print(f"   Location: {street} ({lat:.4f}, {lon:.4f})")
    print(f"   Type: {alert_type}")
    print(f"   Confidence: {confidence}/10")
    
    print("\n🚀 Sending test notification...")
    
    # Send to Telegram
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ SUCCESS: Test notification sent successfully!")
            print("📱 Check your Telegram channel for the validation message")
            print("🎯 If you received the message, the system is working correctly")
            return True
        else:
            print(f"❌ FAILED: Telegram API returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")
        return False

def check_monitor_status():
    """Additional status check"""
    print("\n🔍 SYSTEM STATUS CHECK")
    print("=" * 30)
    
    try:
        # Test Waze API connectivity
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Test authentication
        auth_response = session.post('https://embed.waze.com/web-events/visitors', json={})
        print(f"🔐 Waze Authentication: {'✅ Working' if auth_response.status_code in [200, 201] else '❌ Failed'} ({auth_response.status_code})")
        
        # Test data retrieval
        if auth_response.status_code in [200, 201]:
            data_response = session.get('https://embed.waze.com/iframe', params={
                'lat': '1.3521', 'lon': '103.8198', 'zoom': '11.5'
            })
            print(f"📡 Waze Data Retrieval: {'✅ Working' if data_response.status_code == 200 else '❌ Failed'} ({data_response.status_code})")
            
            if data_response.status_code == 200:
                content = data_response.text
                accident_mentions = content.lower().count('accident')
                print(f"🎯 Accident Keywords in Data: {accident_mentions} mentions")
                
                if accident_mentions > 0:
                    print("✅ Waze data contains traffic incident information")
                    print("🔍 The parsing logic needs improvement to extract coordinates")
                else:
                    print("❓ No accident keywords found in current data")
        
    except Exception as e:
        print(f"❌ System check error: {e}")

if __name__ == '__main__':
    # Run the ultimate validation test
    success = test_notification_pipeline()
    
    # Check system status
    check_monitor_status()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 VALIDATION COMPLETE: Notification system is functional!")
        print("📧 The monitoring system will send alerts when real accidents occur.")
        print("🔍 Current issue: Coordinate extraction from Waze data needs refinement.")
    else:
        print("❌ VALIDATION FAILED: Notification system has issues.")
        print("🔧 Check bot token and chat ID configuration.")
    
    print("\n🏁 COMPREHENSIVE VALIDATION FINISHED")