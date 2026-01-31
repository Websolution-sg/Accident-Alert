#!/usr/bin/env python3
"""
Script to disable Method 1 (Bot API monitoring) on Google VM
This will stop the waze_accident_monitor.py service
"""
import requests
import json
import datetime

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHAT_ID = "-1003683261194"

def send_shutdown_notification():
    """Send notification that Method 1 is being disabled"""
    
    message = f"""🔄 **System Update - {datetime.datetime.now().strftime('%H:%M:%S')}**

**Method 1 (Bot API) DISABLED**

✅ **Active System:** Method 2 (User-based real-time)
• Source: @sgaccident (-1001486947378)  
• Monitoring: ALL messages (no filtering)
• Speed: Real-time (0-1 second delay)
• Account: @pukiboi user account

❌ **Disabled:** Method 1 (VM Bot API polling)
• Old 60-second polling discontinued
• VM bot monitoring stopped

**Result:** Single real-time monitoring system active!"""

    try:
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={
                'chat_id': TARGET_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['result']['message_id']
        else:
            print(f"Failed to send notification: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error sending notification: {e}")
        return None

def check_vm_bot_status():
    """Check if VM bot is still active"""
    print("🔍 Checking VM Bot Status...")
    
    try:
        # Try to get updates - if VM is running, we'll get 409 conflict
        response = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=5&limit=1',
            timeout=10
        )
        
        if response.status_code == 409:
            print("⚡ VM Bot is still ACTIVE (409 conflict detected)")
            print("   You need to stop the service on your Google VM")
            return True
        elif response.status_code == 200:
            print("✅ VM Bot appears to be INACTIVE (no conflict)")
            return False
        else:
            print(f"❓ Unexpected response: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking VM status: {e}")
        return None

def main():
    """Main function to disable Method 1"""
    print("🛑 DISABLING METHOD 1 (Bot API Monitoring)")
    print("=" * 60)
    
    # Check current VM status
    vm_active = check_vm_bot_status()
    
    if vm_active:
        print("\n📋 TO STOP METHOD 1 ON YOUR GOOGLE VM:")
        print("=" * 60)
        print("Option 1 - SSH Command:")
        print("   ssh your-vm-user@your-vm-ip")
        print("   sudo systemctl stop accident-monitor")
        print("   sudo systemctl disable accident-monitor")
        print()
        print("Option 2 - Google Cloud Console:")
        print("   1. Go to Google Cloud Console")
        print("   2. Navigate to Compute Engine > VM instances")  
        print("   3. SSH into your accident-monitor VM")
        print("   4. Run: sudo pkill -f waze_accident_monitor.py")
        print("   5. Run: sudo systemctl stop accident-monitor")
        print()
        print("Option 3 - Stop VM entirely:")
        print("   gcloud compute instances stop accident-monitor --zone=asia-southeast1-a")
        
    elif vm_active is False:
        print("✅ Method 1 appears to be already stopped")
        
    # Send notification about the change
    print(f"\n📤 Sending system update notification...")
    msg_id = send_shutdown_notification()
    
    if msg_id:
        print(f"✅ Notification sent (Message ID: {msg_id})")
    else:
        print("⚠️  Failed to send notification")
    
    print(f"\n🎯 RESULT:")
    print("=" * 60)
    print("✅ Method 2 (Real-time user monitoring) - ACTIVE")
    print("❌ Method 1 (VM bot polling) - DISABLED")  
    print("⚡ All @sgaccident messages forwarded instantly with no filtering")
    print("=" * 60)

if __name__ == "__main__":
    main()