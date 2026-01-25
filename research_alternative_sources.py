#!/usr/bin/env python3
"""
Research and implement alternative data sources for Singapore accident monitoring
This script explores various APIs and services that can provide traffic/accident data
"""
import requests
import json
import time
import datetime

def test_singapore_government_apis():
    """Test available Singapore government data APIs"""
    print("=== Testing Singapore Government APIs ===")
    
    # DataGov.sg APIs
    apis_to_test = [
        {
            'name': 'Traffic Incidents',
            'url': 'https://api.data.gov.sg/v1/transport/traffic-incidents',
            'description': 'Real-time traffic incidents from LTA'
        },
        {
            'name': 'Traffic Images',
            'url': 'https://api.data.gov.sg/v1/transport/traffic-images',
            'description': 'Traffic camera images'
        },
        {
            'name': 'Carpark Availability',
            'url': 'https://api.data.gov.sg/v1/transport/carpark-availability',
            'description': 'Carpark availability (might indicate congestion areas)'
        },
        {
            'name': 'Taxi Availability',
            'url': 'https://api.data.gov.sg/v1/transport/taxi-availability',
            'description': 'Taxi availability (might indicate traffic patterns)'
        }
    ]
    
    for api in apis_to_test:
        print(f"\nTesting: {api['name']}")
        print(f"URL: {api['url']}")
        print(f"Description: {api['description']}")
        
        try:
            response = requests.get(api['url'], timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success! Response size: {len(response.text)} bytes")
                
                # Check for relevant data
                if 'items' in data:
                    items = data['items']
                    if items:
                        print(f"Found {len(items)} items")
                        first_item = items[0]
                        print(f"Sample data keys: {list(first_item.keys())}")
                        
                        # Look for traffic incidents specifically
                        if 'incidents' in first_item:
                            incidents = first_item['incidents']
                            print(f"Found {len(incidents)} incidents")
                            if incidents:
                                print(f"Sample incident: {incidents[0]}")
                    else:
                        print("No items in response")
                else:
                    print(f"Response structure: {list(data.keys())}")
                    
            elif response.status_code == 403:
                print("✗ 403 Forbidden - API key might be required")
            elif response.status_code == 404:
                print("✗ 404 Not Found - Endpoint might not exist")
            else:
                print(f"✗ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
        
        time.sleep(1)  # Rate limiting

def test_lta_datamall():
    """Test Land Transport Authority (LTA) DataMall APIs"""
    print("\n=== Testing LTA DataMall APIs ===")
    print("Note: LTA DataMall requires API key registration")
    print("Register at: https://datamall.lta.gov.sg/content/datamall/en.html")
    
    # These would require API key
    lta_apis = [
        {
            'name': 'Traffic Incidents',
            'url': 'http://datamall2.mytransport.sg/ltaodataservice/TrafficIncidents',
            'description': 'Current traffic incidents and road works'
        },
        {
            'name': 'Traffic Speed Bands',
            'url': 'http://datamall2.mytransport.sg/ltaodataservice/TrafficSpeedBandsv2',
            'description': 'Real-time traffic speed information'
        },
        {
            'name': 'Road Openings',
            'url': 'http://datamall2.mytransport.sg/ltaodataservice/RoadOpenings',
            'description': 'Planned road works and closures'
        }
    ]
    
    api_key = None  # Would need to be obtained from LTA
    
    if not api_key:
        print("⚠ No API key available for LTA DataMall")
        print("To use LTA APIs:")
        print("1. Register at https://datamall.lta.gov.sg/content/datamall/en.html")
        print("2. Get your API key")
        print("3. Add it to the script")
        return
    
    headers = {'AccountKey': api_key}
    
    for api in lta_apis:
        print(f"\nTesting: {api['name']}")
        try:
            response = requests.get(api['url'], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success! Found {len(data.get('value', []))} records")
            else:
                print(f"✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Error: {e}")

def test_alternative_traffic_sources():
    """Test alternative traffic information sources"""
    print("\n=== Testing Alternative Traffic Sources ===")
    
    # Web scraping targets (be respectful with rate limiting)
    sources = [
        {
            'name': 'EMAS (Emergency Monitoring & Advisory System)',
            'url': 'https://www.emas.gov.sg',
            'description': 'Singapore emergency and traffic monitoring'
        },
        {
            'name': 'OneMotoring',
            'url': 'https://www.onemotoring.com.sg',
            'description': 'Official motoring portal with traffic info'
        },
        {
            'name': 'Traffic Police Singapore',
            'url': 'https://www.police.gov.sg',
            'description': 'Official police traffic updates'
        }
    ]
    
    for source in sources:
        print(f"\nTesting: {source['name']}")
        print(f"URL: {source['url']}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(source['url'], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text.lower()
                traffic_keywords = ['accident', 'incident', 'traffic', 'jam', 'closure', 'emergency']
                found_keywords = [kw for kw in traffic_keywords if kw in content]
                
                if found_keywords:
                    print(f"✓ Accessible, contains traffic keywords: {found_keywords}")
                else:
                    print("✓ Accessible, but no obvious traffic keywords found")
                    
                print(f"Content size: {len(response.text)} bytes")
            else:
                print(f"✗ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
        
        time.sleep(2)  # Be respectful with rate limiting

def test_premium_proxy_services():
    """Test premium proxy services for Waze access"""
    print("\n=== Testing Premium Proxy Services ===")
    print("Premium proxy services that could help bypass Waze blocking:")
    
    premium_services = [
        {
            'name': 'Bright Data (formerly Luminati)',
            'url': 'https://brightdata.com',
            'features': ['Residential IPs', 'Datacenter IPs', 'Mobile IPs', 'Rotating proxies'],
            'pricing': 'Starting from $500/month',
            'reliability': 'Very High'
        },
        {
            'name': 'Oxylabs',
            'url': 'https://oxylabs.io',
            'features': ['Residential proxies', 'Datacenter proxies', 'Real-time crawler'],
            'pricing': 'Starting from $300/month',
            'reliability': 'High'
        },
        {
            'name': 'SmartProxy',
            'url': 'https://smartproxy.com',
            'features': ['40M+ residential IPs', 'City-level targeting'],
            'pricing': 'Starting from $75/month',
            'reliability': 'Good'
        },
        {
            'name': 'ProxyMesh',
            'url': 'https://proxymesh.com',
            'features': ['Rotating proxies', 'World-wide servers'],
            'pricing': 'Starting from $10/month',
            'reliability': 'Basic'
        }
    ]
    
    for service in premium_services:
        print(f"\n{service['name']}:")
        print(f"  URL: {service['url']}")
        print(f"  Features: {', '.join(service['features'])}")
        print(f"  Pricing: {service['pricing']}")
        print(f"  Reliability: {service['reliability']}")

def generate_implementation_plan():
    """Generate implementation plan for alternative data sources"""
    print("\n=== IMPLEMENTATION RECOMMENDATIONS ===")
    
    print("\n1. IMMEDIATE SOLUTIONS (Free/Low Cost):")
    print("   - Continue monitoring @sgaccident Telegram channel (working)")
    print("   - Implement Singapore government APIs (free, official)")
    print("   - Register for LTA DataMall API key (free, official)")
    print("   - Add web scraping for EMAS updates (with rate limiting)")
    
    print("\n2. MEDIUM-TERM SOLUTIONS:")
    print("   - Subscribe to premium proxy service (SmartProxy ~$75/month)")
    print("   - Implement Twitter/X API monitoring for traffic hashtags")
    print("   - Add RSS feed monitoring from traffic websites")
    
    print("\n3. LONG-TERM SOLUTIONS:")
    print("   - Consider Bright Data for enterprise-grade proxy (if high volume)")
    print("   - Develop partnerships with local traffic data providers")
    print("   - Implement ML-based traffic pattern prediction")
    
    print("\n4. CODE CHANGES NEEDED:")
    print("   - Add LTA DataMall integration")
    print("   - Implement Singapore gov API parsing")
    print("   - Add proxy configuration system")
    print("   - Create failover logic between data sources")

def main():
    """Main research function"""
    print("Singapore Traffic Data Sources Research")
    print("=" * 50)
    
    # Run all tests
    test_singapore_government_apis()
    test_lta_datamall()
    test_alternative_traffic_sources()
    test_premium_proxy_services()
    generate_implementation_plan()
    
    print("\n" + "=" * 50)
    print("Research complete! Check the recommendations above.")

if __name__ == "__main__":
    main()