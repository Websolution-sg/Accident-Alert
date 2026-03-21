# Final System Configuration - Singapore Accident Monitor

## 🎯 System Overview
Dual monitoring system for Singapore accident alerts with enhanced location detection.

## 📁 Final Files Structure

### **Active Production Files:**
- **`simple_waze_monitor_final.py`** - Final Waze accident monitor
  - Simple format: "Accident on [location]" with enhanced fallback
  - **NEW:** Expressway accidents include area context (e.g., "PIE, Tampines area")
  - Selective location enhancement for unknown locations only
  - Real-time filtering (15-minute age limit)
  - Duplicate prevention with coordinate-based IDs

- **`telethon_sgaccident_forwarder_final.py`** - Final @sgaccident forwarder  
  - Preserves exact first-line headers from @sgaccident channel
  - Real-time forwarding with 0-1 second delivery
  - Enhanced coordinate extraction

### **Utility Files:**
- **`check_and_restart_monitoring.py`** - System monitoring utility
- **`pukiboi_session.session`** - Telethon authentication session
- **`processed_waze_accidents.json`** - Waze duplicate prevention state
- **`telegram_offset.json`** - Telegram message offset state

## 🚀 Active Deployment Status

### **Google Cloud VM: `sg-accident-monitor`**
- **Zone:** us-central1-a
- **Machine:** e2-micro  
- **Status:** RUNNING

### **Active Processes:**
1. **Waze Monitor** (PID 114044)
   - File: `simple_waze_monitor_enhanced_expressways.py`
   - Format: Simple "Accident on [location]" with smart fallback
   - **Enhancement:** Expressway accidents show area context (e.g., "PIE, Tampines area")
   - Frequency: 60-second checks
   - Age Filter: 15 minutes maximum

2. **Telethon Forwarder** (PID 110493)
   - File: `telethon_first_line_header.py`
   - Format: Preserved @sgaccident first-line headers
   - Mode: Real-time event listener

### **Target Channel:**
- **Channel:** 🇸🇬Sg accidents (`-1003683261194`)
- **Posting Rate:** Real-time (immediate for new accidents)

## 🔧 Location Detection Logic

### **Priority Order:**
1. **Original Format** (Primary)
   - Good street name → `"Accident on [Street Name]"`
   - City available → `"Accident on [City]"`
   - Street + City → `"Accident on [Street], [City]"`

2. **Enhanced Fallback** (Only for unknown)
   - Expressway detection → `"Accident on PIE, Tampines area"`, `"Accident on CTE, Ang Mo Kio area"`  
   - Area mapping → `"Accident on Tampines area"`, `"Accident on Marina Bay area"`
   - Regional fallback → `"Accident on Eastern Singapore"`
   - Coordinates → `"Accident on coordinates 1.3456, 103.7890"`

## 🎯 Key Features
- **Duplicate Prevention:** Coordinate-based ID system
- **Real-time Filtering:** Only posts accidents < 15 minutes old
- **Singapore Bounds:** Geographic filtering for Singapore only
- **Enhanced Coordinates:** Improved location detection for @sgaccident messages
- **Dual Source:** Waze API + @sgaccident Telegram channel
- **Simple Format:** "Accident on [location]" style maintained

## 📊 Performance
- **Latency:** 0-1 second for Telethon, 60-second cycle for Waze
- **Accuracy:** Enhanced coordinate extraction and location mapping
- **Reliability:** Proper error handling and session management
- **Coverage:** Complete Singapore accident monitoring

---
**Last Updated:** February 8, 2026 - 16:40 SGT  
**Enhancement:** Expressway accidents now include area context  
**System Status:** ✅ Fully Operational