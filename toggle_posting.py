#!/usr/bin/env python3
"""
Toggle Telegram posting on/off for accident monitoring
"""
import os
import sys

def toggle_posting(enable=None):
    """Toggle posting in the monitoring script"""
    script_file = "waze_accident_monitor.py"
    
    if not os.path.exists(script_file):
        print(f"❌ {script_file} not found")
        return
    
    with open(script_file, 'r') as f:
        content = f.read()
    
    # Check current state
    is_disabled = "# POSTING DISABLED" in content
    
    if enable is None:
        # Toggle current state
        enable = is_disabled
    
    if enable and is_disabled:
        print("🔄 Enabling Telegram posting...")
        # Replace disabled version with active version
        content = content.replace(
            '        # POSTING DISABLED - Channel stopped by user request\n        print(f"📵 POSTING DISABLED - Would have sent: {message[:100]}...")\n        return True  # Return True to continue normal flow without actually sending',
            '        url = f"{self.telegram_api_url}/sendMessage"\n        \n        payload = {\n            \'chat_id\': self.telegram_channel_id,\n            \'text\': message,\n            \'parse_mode\': \'Markdown\',\n            \'disable_web_page_preview\': False\n        }\n        \n        try:\n            response = requests.post(url, json=payload, timeout=10)\n            response.raise_for_status()\n            return True\n        except requests.RequestException as e:\n            print(f"Error sending Telegram message: {e}")\n            return False'
        )
        print("✅ Telegram posting ENABLED")
        
    elif not enable and not is_disabled:
        print("🔄 Disabling Telegram posting...")
        # Replace active version with disabled version
        content = content.replace(
            '        url = f"{self.telegram_api_url}/sendMessage"\n        \n        payload = {\n            \'chat_id\': self.telegram_channel_id,\n            \'text\': message,\n            \'parse_mode\': \'Markdown\',\n            \'disable_web_page_preview\': False\n        }\n        \n        try:\n            response = requests.post(url, json=payload, timeout=10)\n            response.raise_for_status()\n            return True\n        except requests.RequestException as e:\n            print(f"Error sending Telegram message: {e}")\n            return False',
            '        # POSTING DISABLED - Channel stopped by user request\n        print(f"📵 POSTING DISABLED - Would have sent: {message[:100]}...")\n        return True  # Return True to continue normal flow without actually sending'
        )
        print("✅ Telegram posting DISABLED")
        
    else:
        if is_disabled:
            print("ℹ️  Telegram posting is already DISABLED")
        else:
            print("ℹ️  Telegram posting is already ENABLED")
        return
    
    # Write back the modified content
    with open(script_file, 'w') as f:
        f.write(content)

def main():
    print("🎛️  Telegram Posting Control")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['on', 'enable', 'start']:
            toggle_posting(True)
        elif arg in ['off', 'disable', 'stop']:
            toggle_posting(False)
        else:
            print("Usage: python toggle_posting.py [on|off|enable|disable|start|stop]")
    else:
        # Interactive mode
        print("Current status check...")
        with open("waze_accident_monitor.py", 'r') as f:
            content = f.read()
        
        is_disabled = "# POSTING DISABLED" in content
        status = "DISABLED" if is_disabled else "ENABLED"
        print(f"Telegram posting is currently: {status}")
        
        choice = input("\nToggle posting? (y/n): ").lower()
        if choice in ['y', 'yes']:
            toggle_posting()

if __name__ == "__main__":
    main()