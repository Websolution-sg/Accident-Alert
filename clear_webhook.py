#!/usr/bin/env python3
"""
Clear Telegram Bot Webhook and Check Status - Secondary Channel
This script helps diagnose and fix 409 conflicts with Telegram bots
"""
import requests
import json

# Secondary channel bot token (primary bot for this setup)
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"

def check_and_clear_webhook(bot_token, bot_name):
    """Check and clear webhook for a bot"""
    print(f"\n=== {bot_name} Bot Status ===")
    
    # Get webhook info
    webhook_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    try:
        response = requests.get(webhook_url, timeout=10)
        webhook_info = response.json()
        
        if webhook_info.get('ok'):
            webhook_data = webhook_info.get('result', {})
            webhook_active = webhook_data.get('url', '')
            pending_updates = webhook_data.get('pending_update_count', 0)
            
            print(f"Webhook URL: {webhook_active or 'None (polling mode)'}")
            print(f"Pending updates: {pending_updates}")
            
            if webhook_active:
                print("🔧 Clearing webhook to enable polling...")
                clear_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
                clear_response = requests.post(clear_url, timeout=10)
                if clear_response.json().get('ok'):
                    print("✅ Webhook cleared successfully")
                else:
                    print("❌ Failed to clear webhook")
            else:
                print("✅ Already in polling mode (no webhook)")
                
        else:
            print(f"❌ Error getting webhook info: {webhook_info.get('description')}")
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    
    # Get bot info
    bot_info_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        response = requests.get(bot_info_url, timeout=10)
        bot_info = response.json()
        
        if bot_info.get('ok'):
            bot_data = bot_info.get('result', {})
            print(f"Bot username: @{bot_data.get('username')}")
            print(f"Bot name: {bot_data.get('first_name')}")
        else:
            print(f"❌ Error getting bot info: {bot_info.get('description')}")
            
    except requests.RequestException as e:
        print(f"❌ Network error getting bot info: {e}")

def main():
    print("🔧 Telegram Bot Webhook Cleaner - Secondary Channel")
    print("=" * 50)
    
    # Check secondary channel bot only
    check_and_clear_webhook(BOT_TOKEN, "Secondary Channel")
    
    print("\n🎯 Summary:")
    print("- Webhook has been cleared for polling mode")
    print("- This should resolve 409 conflicts")
    print("- You can now run your monitoring script for secondary channel")

if __name__ == "__main__":
    main()