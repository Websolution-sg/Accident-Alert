#!/usr/bin/env python3

import requests
import json

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"

def check_webhook():
    """Check if bot has webhook configured"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Webhook Info:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Failed to get webhook info: {response.text}")
            return None
    except Exception as e:
        print(f"Error checking webhook: {e}")
        return None

def delete_webhook():
    """Delete webhook to use getUpdates instead"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            data = response.json()
            print("Delete Webhook Result:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Failed to delete webhook: {response.text}")
            return None
    except Exception as e:
        print(f"Error deleting webhook: {e}")
        return None

def test_get_updates():
    """Test getUpdates to see if it works now"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"limit": 1, "timeout": 5}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("GetUpdates Test Result:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Failed to get updates: {response.text}")
            return None
    except Exception as e:
        print(f"Error testing getUpdates: {e}")
        return None

if __name__ == "__main__":
    print("=== TELEGRAM BOT CONFLICT DIAGNOSIS ===\n")
    
    # Check webhook
    webhook_info = check_webhook()
    
    # If webhook is set, delete it
    if webhook_info and webhook_info.get('result', {}).get('url'):
        print(f"\nWebhook found: {webhook_info['result']['url']}")
        print("Deleting webhook to use getUpdates...")
        delete_webhook()
    else:
        print("No webhook configured")
    
    print("\nTesting getUpdates...")
    test_get_updates()