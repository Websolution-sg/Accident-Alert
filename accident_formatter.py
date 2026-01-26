#!/usr/bin/env python3
import re
import datetime

# Configuration for coordinate detection
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

def is_within_singapore(lat, lon):
    """Check if coordinates are within Singapore bounds"""
    if not lat or not lon:
        return False
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return (SINGAPORE_BOUNDS["south"] <= lat_f <= SINGAPORE_BOUNDS["north"] and 
                SINGAPORE_BOUNDS["west"] <= lon_f <= SINGAPORE_BOUNDS["east"])
    except (ValueError, TypeError):
        return False

def extract_coordinates_from_text(text):
    """Extract coordinates from text using various patterns"""
    if not text:
        return None, None
    
    # Pattern 1: Standard decimal degrees (1.234567, 103.789012)
    pattern1 = r'(\d+\.\d+),\s*(\d+\.\d+)'
    match1 = re.search(pattern1, text)
    if match1:
        lat, lon = float(match1.group(1)), float(match1.group(2))
        if is_within_singapore(lat, lon):
            return lat, lon
    
    # Pattern 2: Coordinates in parentheses or different formats
    pattern2 = r'\(?(\d+\.\d+)\s*[,\s]\s*(\d+\.\d+)\)?'
    matches2 = re.finditer(pattern2, text)
    for match in matches2:
        lat, lon = float(match.group(1)), float(match.group(2))
        if is_within_singapore(lat, lon):
            return lat, lon
    
    return None, None

def format_accident_message(original_text, coordinates=None):
    """Format accident message for manual posting"""
    message = "🚨 <b>ACCIDENT ALERT</b> 🚨\n\n"
    
    # Add the original message content
    message += f"📄 <b>Details:</b> {original_text}\n"
    
    # Add coordinates if available
    if coordinates and len(coordinates) == 2:
        lat, lon = coordinates
        message += f"🗺️ <b>Coordinates:</b> {lat}, {lon}\n"
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        message += f"🔗 <b>View on Maps:</b> <a href='{maps_url}'>Open Location</a>\n"
    
    message += f"⏰ <b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"🔗 <b>Source:</b> @sgaccident Channel"
    
    return message

def process_accident_text(input_text):
    """Process pasted accident text and return formatted version"""
    print("=" * 60)
    print("🔄 PROCESSING ACCIDENT TEXT")
    print("=" * 60)
    
    # Extract coordinates
    lat, lon = extract_coordinates_from_text(input_text)
    
    if lat and lon:
        print(f"✅ Found coordinates: {lat}, {lon}")
        print(f"🗺️ Google Maps: https://www.google.com/maps?q={lat},{lon}")
    else:
        print("⚠️ No valid Singapore coordinates found")
    
    # Format the message
    formatted = format_accident_message(input_text, (lat, lon) if lat and lon else None)
    
    print("\n📋 FORMATTED MESSAGE FOR YOUR CHANNEL:")
    print("-" * 40)
    print(formatted)
    print("-" * 40)
    
    return formatted

def main():
    """Interactive accident text processor"""
    print("🚨 ACCIDENT TEXT FORMATTER 🚨")
    print("=" * 50)
    print()
    print("📋 HOW TO USE:")
    print("1. Visit: https://web.telegram.org/a/#-1001486947378")
    print("2. Find recent accident posts in @sgaccident channel")
    print("3. Copy the accident text")
    print("4. Paste it here to get formatted version")
    print("5. Copy the formatted text to your own channel")
    print()
    print("✨ FEATURES:")
    print("• Extracts coordinates automatically")
    print("• Adds Google Maps links")
    print("• Formats with proper styling")
    print("• Adds timestamps")
    print()
    
    while True:
        print("=" * 50)
        choice = input("Enter 'f' to format text, 'h' for help, or 'q' to quit: ").lower().strip()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == 'h':
            print("\n📖 HELP:")
            print("• Copy accident text from @sgaccident")
            print("• Paste it when prompted")
            print("• Get formatted version with maps links")
            print("• Manually post the formatted text to your channel")
            print()
        elif choice == 'f':
            print("\n📥 Paste the accident text from @sgaccident:")
            print("(Type your text and press Enter, then type 'END' and press Enter)")
            
            lines = []
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            
            if lines:
                input_text = "\n".join(lines).strip()
                if input_text:
                    formatted = process_accident_text(input_text)
                    print("\n✅ Copy the formatted message above and paste it into your channel!")
                else:
                    print("❌ No text entered.")
            else:
                print("❌ No text entered.")
        else:
            print("❌ Invalid choice. Use 'f', 'h', or 'q'")

if __name__ == "__main__":
    main()