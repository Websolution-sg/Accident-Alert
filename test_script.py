#!/usr/bin/env python3

print("Testing script startup...")

try:
    import requests
    import json
    import time
    import datetime
    import os
    import re
    from urllib.parse import urlencode
    print("All imports successful")
    
    # Test bot token (hidden)
    bot_token = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
    print("Bot token loaded")
    
    # Test file loading
    try:
        with open('processed_accidents.json', 'r') as f:
            data = json.load(f)
            processed_waze = set(data.get('waze_accidents', []))
            print(f"Processed accidents loaded: {len(processed_waze)} items")
    except Exception as e:
        print(f"Error loading processed accidents: {e}")
    
    print("Script test completed successfully!")
    
except Exception as e:
    print(f"Error during script test: {e}")
    import traceback
    traceback.print_exc()