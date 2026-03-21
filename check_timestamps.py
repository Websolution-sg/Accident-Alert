import requests
import json
from datetime import datetime
import pytz

url = 'https://www.waze.com/live-map/api/georss'
params = {
    'format': 'JSON',
    'bbox': '103.5,1.2,104.1,1.5',
    'types': 'accidents'
}

try:
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    accidents = data.get('alerts', [])
    
    sgt = pytz.timezone('Asia/Singapore')
    current_time = datetime.now(sgt)
    
    print('=== WAZE ACCIDENT TIMESTAMP ANALYSIS ===')
    print(f'Current time: {current_time.strftime("%Y-%m-%d %H:%M:%S SGT")}')
    print(f'Total accidents: {len(accidents)}')
    print('')
    
    for i, accident in enumerate(accidents[:3], 1):
        print(f'Accident {i}:')
        print(f'  Available fields: {list(accident.keys())}')
        
        pub_millis = accident.get('pubMillis')
        if pub_millis:
            pub_time = datetime.fromtimestamp(pub_millis / 1000, tz=sgt)
            age_minutes = (current_time - pub_time).total_seconds() / 60
            print(f'  Published: {pub_time.strftime("%Y-%m-%d %H:%M:%S SGT")}')
            print(f'  Age: {age_minutes:.1f} minutes old')
            
            if age_minutes < 30:
                print(f'  Status: RECENT (< 30 min) - SHOULD POST')
            else:
                print(f'  Status: OLD (> 30 min) - SHOULD FILTER OUT')
        else:
            print(f'  No timestamp available')
            
        print(f'  Location: {accident.get("street", "Unknown")}')
        print('')
        
except Exception as e:
    print(f'Error: {e}')