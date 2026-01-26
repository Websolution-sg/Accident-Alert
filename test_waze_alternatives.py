#!/usr/bin/env python3
"""
Alternative Waze accident data collection via web scraping
Since the official Waze API is blocked (403 Forbidden), this provides 
a backup method to collect accident data from alternative sources.
"""
import requests
import json
import time
import re
from typing import List, Dict

def get_singapore_traffic_info():
    """
    Get traffic incidents from alternative sources
    This is a backup when Waze API is blocked
    """
    print("🔍 Checking alternative traffic data sources...")
    
    # LTA Traffic Incidents API (if available)
    try:
        # Singapore LTA DataMall might have incident data
        print("   Trying Singapore government traffic data...")
        
        # Note: This would require LTA API key - placeholder for now
        # You can register at https://datamall.lta.gov.sg/content/datamall/en.html
        # incidents_url = "http://datamall2.mytransport.sg/ltaodataservice/TrafficIncidents"
        
        print("   LTA API requires registration - placeholder")
        
    except Exception as e:
        print(f"   Error with LTA data: {e}")
    
    # Check traffic.gov.sg for incidents
    try:
        print("   Checking traffic.gov.sg for incidents...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # This is a placeholder - the actual implementation would need
        # to parse the traffic.gov.sg website structure
        response = requests.get('https://www.traffic.gov.sg', headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"   Successfully accessed traffic.gov.sg (status: {response.status_code})")
            print("   Note: Would need to implement HTML parsing for actual incident data")
        else:
            print(f"   Failed to access traffic.gov.sg (status: {response.status_code})")
            
    except Exception as e:
        print(f"   Error accessing traffic.gov.sg: {e}")
    
    print("\n📝 WAZE API STATUS:")
    print("   The Waze API is currently blocked (403 Forbidden)")
    print("   This is common as Waze restricts third-party access")
    print("   Your system will continue monitoring @sgaccident channel")
    print("   Consider setting up LTA DataMall API for additional traffic data")
    
    return []

def check_waze_api_status():
    """Check if Waze API is accessible"""
    waze_url = "https://www.waze.com/live-map/api/georss"
    params = {
        'bottom': 1.1304753,
        'left': 103.6055424,
        'right': 104.0945619,
        'top': 1.4764671,
        'env': 'row',
        'types': 'alerts,traffic'
    }
    
    try:
        response = requests.get(waze_url, params=params, timeout=10)
        if response.status_code == 200:
            print("✅ Waze API is accessible")
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"   Found {len(alerts)} alerts")
            return True
        else:
            print(f"❌ Waze API blocked (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Waze API error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING WAZE DATA COLLECTION ALTERNATIVES")
    print("=" * 60)
    
    # Check official Waze API first
    waze_working = check_waze_api_status()
    
    print("\n" + "-" * 40)
    
    # Try alternative sources
    if not waze_working:
        get_singapore_traffic_info()
    
    print("\n" + "=" * 60)
    print("✅ Alternative data source test completed")