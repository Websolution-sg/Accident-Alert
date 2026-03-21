#!/usr/bin/env python3
from datetime import datetime
import pytz
import json

# Current Singapore time  
sgt = pytz.timezone('Asia/Singapore')
now = datetime.now(sgt)
hour = now.hour

print('=== WAZE FILTERING ANALYSIS ===')
print(f'Current SGT time: {now.strftime("%Y-%m-%d %H:%M:%S")}')
print(f'Current hour: {hour}')
print('')

# Load processed accidents
try:
    with open('/tmp/processed_waze_accidents.json', 'r') as f:
        processed = json.load(f)
    print(f'Processed accidents: {len(processed)}')
    for acc in processed:
        print(f'  - {acc}')
    print('')
except Exception as e:
    print(f'Error loading processed accidents: {e}')
    processed = []

# Check what IDs would be generated now
print('=== ID GENERATION TEST ===')
coords = [(1.365, 103.780), (1.374, 103.895), (1.353, 103.876)]

for lat, lng in coords:
    today = now.strftime('%Y%m%d')
    current_id = f'waze_coord_{lat}_{lng}_{today}_{hour}'
    is_duplicate = current_id in processed
    
    print(f'Coordinates: {lat}, {lng}')
    print(f'  Generated ID: {current_id}')
    print(f'  Would be duplicate: {is_duplicate}')
    print('')

print('=== POTENTIAL ISSUES ===')
print('If the same coordinates are being found but IDs are different,')
print('then NEW accidents should be posted, not marked as duplicates.')
print('')
print('If accidents from hours 18/19 are still appearing and being')
print('correctly filtered, then the system is working properly.')