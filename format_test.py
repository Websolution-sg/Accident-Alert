#!/usr/bin/env python3
"""Test script for format comparison"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Set
import os
import re

class FormatTester:
    def __init__(self):
        pass
    
    def format_accident_message(self, accident: Dict) -> str:
        street = accident.get('street', 'Unknown location')
        lat = accident.get('location', {}).get('y', 0)
        lon = accident.get('location', {}).get('x', 0)
        
        message = f"🚨 *ACCIDENT ALERT*\n\n"
        message += f"📍 *Location:* {street}\n"
        message += f"⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}\n"
        
        if lat and lon:
            message += f"🗺️ *Google Maps:* https://maps.google.com/?q={lat},{lon}\n"
            message += f"🚗 *Waze:* https://waze.com/ul?ll={lat}%2C{lon}&navigate=yes\n"
        
        message += f"\n🔗 *Source:* Waze Live Map"
        return message
    
    def format_sgaccident_message(self, location, coords=None) -> str:
        """Format @sgaccident message in Waze-compatible format"""
        # Extract street name from location (use same logic as Waze)
        if isinstance(location, tuple):  # coordinates
            lat, lon = location
            street = f"{lat:.4f}, {lon:.4f}"
        else:  # address text
            street = location if location else 'Unknown location'
        
        # Use exact same format as Waze accidents
        message = f"🚨 *ACCIDENT ALERT*\n\n"
        message += f"📍 *Location:* {street}\n"
        message += f"⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}\n"
        
        # Add map links if coordinates available
        if coords or isinstance(location, tuple):
            if isinstance(location, tuple):
                lat, lon = location
            else:
                lat, lon = coords
            message += f"🗺️ *Google Maps:* https://maps.google.com/?q={lat},{lon}\n"
            message += f"🚗 *Waze:* https://waze.com/ul?ll={lat}%2C{lon}&navigate=yes\n"
        
        # Only difference: source attribution
        message += f"\n🔗 *Source:* @sgaccident Community"
        return message

# Test the formats
tester = FormatTester()

print("=== Waze Format ===")
waze_msg = tester.format_accident_message({
    'street': 'Orchard Road', 
    'location': {'x': 103.8198, 'y': 1.3048}
})
print(waze_msg)

print("\n=== @sgaccident Format (with address) ===")
sg_msg = tester.format_sgaccident_message('Orchard Road', (1.3048, 103.8198))
print(sg_msg)

print("\n=== @sgaccident Format (coordinates only) ===")
sg_msg2 = tester.format_sgaccident_message((1.3048, 103.8198))
print(sg_msg2)