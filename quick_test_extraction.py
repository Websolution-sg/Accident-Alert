import requests
import json
import datetime

TELEGRAM_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SOURCE_CHANNEL = "-1001486947378"  # @sgaccident
TARGET_CHANNEL = "-1003683261194"  # Your channel

print("=== TESTING @SGACCIDENT EXTRACTION ===")

# Get recent updates
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
response = requests.get(url, params={'limit': 100}, timeout=10)

if response.status_code == 200:
    data = response.json()
    if data.get('ok'):
        updates = data.get('result', [])
        print(f"Total updates: {len(updates)}")
        
        # Look for @sgaccident posts
        sgaccident_posts = []
        for update in updates:
            if 'channel_post' in update:
                post = update['channel_post']
                chat = post.get('chat', {})
                if str(chat.get('id')) == SOURCE_CHANNEL:
                    sgaccident_posts.append(post)
        
        print(f"@sgaccident posts found: {len(sgaccident_posts)}")
        
        if sgaccident_posts:
            print("\nRecent posts:")
            for i, post in enumerate(sgaccident_posts[-3:], 1):
                text = post.get('text', 'No text')[:80]
                date = datetime.datetime.fromtimestamp(post.get('date', 0))
                print(f"{i}. [{date}] {text}...")
        
        # Test sending a sample message
        if sgaccident_posts:
            latest_post = sgaccident_posts[-1]
            sample_text = latest_post.get('text', 'Test message')
            
            test_message = f"""🚨 <b>TEST REPOST FROM @SGACCIDENT</b>

📍 <b>Sample Content:</b>
{sample_text}

⏰ <b>Test Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔗 <b>Source:</b> @sgaccident (Test)"""
            
            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                'chat_id': TARGET_CHANNEL,
                'text': test_message,
                'parse_mode': 'HTML'
            }
            
            send_response = requests.post(send_url, json=payload, timeout=10)
            if send_response.status_code == 200:
                print("\n✅ TEST MESSAGE SENT SUCCESSFULLY!")
                print("Check your channel: https://web.telegram.org/a/#-1003683261194")
            else:
                print(f"\n❌ Failed to send test message: {send_response.status_code}")
                print(send_response.text)
    else:
        print(f"API Error: {data.get('description')}")
else:
    print(f"HTTP Error: {response.status_code}")