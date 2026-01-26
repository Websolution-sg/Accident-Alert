#!/usr/bin/env python3
"""Deploy Singapore Government API version to Google Cloud VM"""
import subprocess
import sys
import os

def deploy_government_version():
    """Deploy the version with Singapore government APIs"""
    print("DEPLOYING SINGAPORE GOVERNMENT API VERSION")
    print("=" * 50)
    
    print("This version uses:")
    print("✓ Singapore government traffic camera API")
    print("✓ Singapore taxi availability API (for congestion detection)")
    print("✓ Singapore Police website monitoring")
    print("✓ @sgaccident Telegram channel (working)")
    print("✓ Waze API attempts (as backup when available)")
    print()
    
    # Upload the government API version
    print("1. Uploading government API version...")
    upload_cmd = [
        "gcloud", "compute", "scp",
        "waze_accident_monitor_gov.py",
        "waze-monitor:~/waze_accident_monitor.py",  # Replace the existing file
        "--zone=asia-southeast1-a"
    ]
    
    try:
        result = subprocess.run(upload_cmd, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print("✓ Government API version uploaded successfully")
        else:
            print(f"✗ Upload failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return False
    
    # Restart the service
    print("\n2. Restarting monitoring service...")
    restart_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=sudo systemctl restart accident-monitor"
    ]
    
    try:
        result = subprocess.run(restart_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Service restarted successfully")
        else:
            print(f"✗ Service restart failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Service restart error: {e}")
        return False
    
    # Check service status
    print("\n3. Checking service status...")
    status_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=sudo systemctl status accident-monitor --no-pager -l"
    ]
    
    try:
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if "active (running)" in result.stdout:
            print("✓ Service is running with government API version")
        else:
            print("✗ Service not running properly")
    except Exception as e:
        print(f"✗ Status check error: {e}")
    
    # Test government APIs from VM
    print("\n4. Testing Singapore government APIs from VM...")
    test_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=python3 -c \"import requests; print('Testing SG Gov APIs...'); r1 = requests.get('https://api.data.gov.sg/v1/transport/traffic-images', timeout=10); print(f'Traffic Images API: {r1.status_code}'); r2 = requests.get('https://api.data.gov.sg/v1/transport/taxi-availability', timeout=10); print(f'Taxi Availability API: {r2.status_code}')\"",
    ]
    
    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        print("Government API test results:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"✗ API test error: {e}")
    
    # View initial logs
    print("\n5. Viewing recent logs...")
    logs_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=sudo journalctl -u accident-monitor -n 30 --no-pager"
    ]
    
    try:
        result = subprocess.run(logs_cmd, capture_output=True, text=True)
        print("Recent service logs:")
        print(result.stdout)
    except Exception as e:
        print(f"✗ Logs viewing error: {e}")
    
    return True

def main():
    """Main deployment process"""
    success = deploy_government_version()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ DEPLOYMENT COMPLETE!")
        print("\nThe monitoring service now uses:")
        print("- Singapore government traffic cameras (reliable)")
        print("- Singapore taxi availability analysis (congestion detection)")
        print("- Singapore Police website monitoring")
        print("- @sgaccident Telegram channel (confirmed working)")
        print("- Waze API attempts as backup (may work occasionally)")
        
        print("\nMonitoring commands:")
        print("• Live logs: gcloud compute ssh waze-monitor --zone=asia-southeast1-a --command='sudo journalctl -u accident-monitor -f'")
        print("• Service status: gcloud compute ssh waze-monitor --zone=asia-southeast1-a --command='sudo systemctl status accident-monitor'")
        print("• Restart service: gcloud compute ssh waze-monitor --zone=asia-southeast1-a --command='sudo systemctl restart accident-monitor'")
        
        print("\nExpected behavior:")
        print("- Government APIs should provide steady traffic monitoring")
        print("- @sgaccident channel will forward relevant accidents")
        print("- Waze may work occasionally when not blocked")
        print("- Check logs to see which sources are working")
        
    else:
        print("✗ DEPLOYMENT FAILED!")
        print("Check the error messages above and try again.")

if __name__ == "__main__":
    main()