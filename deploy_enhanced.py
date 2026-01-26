#!/usr/bin/env python3
"""Deploy enhanced anti-blocking version to Google Cloud VM"""
import subprocess
import sys
import os

def upload_enhanced_version():
    """Upload the enhanced version with anti-blocking to the VM"""
    print("Uploading enhanced accident monitor with anti-blocking...")
    
    # Upload the enhanced version
    upload_cmd = [
        "gcloud", "compute", "scp",
        "waze_accident_monitor.py",
        "waze-monitor:~/waze_accident_monitor.py",
        "--zone=asia-southeast1-a"
    ]
    
    try:
        result = subprocess.run(upload_cmd, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print("✓ Enhanced version uploaded successfully")
        else:
            print(f"✗ Upload failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return False
    
    return True

def restart_service():
    """Restart the monitoring service on the VM"""
    print("Restarting monitoring service...")
    
    restart_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=sudo systemctl restart accident-monitor"
    ]
    
    try:
        result = subprocess.run(restart_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Service restarted successfully")
            return True
        else:
            print(f"✗ Service restart failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Service restart error: {e}")
        return False

def check_service_status():
    """Check if the service is running properly"""
    print("Checking service status...")
    
    status_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=sudo systemctl status accident-monitor --no-pager -l"
    ]
    
    try:
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        print("Service status:")
        print(result.stdout)
        
        if "active (running)" in result.stdout:
            print("✓ Service is running")
            return True
        else:
            print("✗ Service not running properly")
            return False
    except Exception as e:
        print(f"✗ Status check error: {e}")
        return False

def view_recent_logs():
    """View recent logs to verify anti-blocking is working"""
    print("Viewing recent logs...")
    
    logs_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=sudo journalctl -u accident-monitor -n 20 --no-pager"
    ]
    
    try:
        result = subprocess.run(logs_cmd, capture_output=True, text=True)
        print("Recent logs:")
        print(result.stdout)
    except Exception as e:
        print(f"✗ Logs viewing error: {e}")

def test_waze_api_on_vm():
    """Test the Waze API directly on the VM"""
    print("Testing Waze API on VM...")
    
    test_cmd = [
        "gcloud", "compute", "ssh", "waze-monitor",
        "--zone=asia-southeast1-a",
        "--command=cd ~ && python3 -c \"import requests; print('Testing Waze API...'); r = requests.get('https://www.waze.com/live-map/api/georss?bottom=1.1304&top=1.4784&left=103.5000&right=104.1000&env=row&types=alerts', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10); print(f'Status: {r.status_code}, Content length: {len(r.text)}')\"",
    ]
    
    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        print("Waze API test result:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"✗ API test error: {e}")

def main():
    """Main deployment process"""
    print("Enhanced Waze Anti-Blocking Deployment")
    print("=" * 50)
    
    steps = [
        ("Upload enhanced version", upload_enhanced_version),
        ("Restart service", restart_service),
        ("Check service status", check_service_status),
        ("Test Waze API on VM", test_waze_api_on_vm),
        ("View recent logs", view_recent_logs)
    ]
    
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        try:
            success = step_func()
            if success is False:
                print(f"⚠ Warning: {step_name} had issues")
        except Exception as e:
            print(f"✗ Error in {step_name}: {e}")
        
        print()  # Add spacing between steps
    
    print("=" * 50)
    print("Deployment complete!")
    print("\nMonitoring Tips:")
    print("1. Watch logs with: gcloud compute ssh waze-monitor --zone=asia-southeast1-a --command='sudo journalctl -u accident-monitor -f'")
    print("2. Check status with: gcloud compute ssh waze-monitor --zone=asia-southeast1-a --command='sudo systemctl status accident-monitor'")
    print("3. Test manually with: python3 test_enhanced_waze.py")

if __name__ == "__main__":
    main()