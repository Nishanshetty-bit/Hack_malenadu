import requests
import time
import json

API = "http://localhost:8000"

def verify():
    print("--- 1. Resetting Database ---")
    requests.post(f"{API}/reset")
    
    print("--- 2. Loading Synthetic Seeded Data ---")
    res = requests.post(f"{API}/load-samples")
    if res.status_code == 200:
        print(f"Successfully loaded {res.json()['total_processed']} reviews.")
    else:
        print("Failed to load samples.")
        return

    print("--- 3. Fetching Smartwatch Trends (Last 14 Days) ---")
    # Using 14 days ago for the seed
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    res = requests.get(f"{API}/trends?category=Smartwatch&start_date={start_date}&end_date={end_date}")
    trends = res.json()
    print(f"Status: {trends['status']}")
    print(f"Anomalies detected: {len(trends['alerts'])}")
    
    for alert in trends['alerts']:
        print(f"  [{alert['severity'].upper()}] Feature: {alert['feature']} | Team: {alert['assigned_team']}")
        print(f"  Msg: {alert['message']}")

    print("\n--- 4. Checking Persistent Action Center (All Open Alerts) ---")
    res = requests.get(f"{API}/alerts?status=open")
    alerts = res.json()['alerts']
    print(f"Total Open Alerts in DB: {len(alerts)}")
    
    # Check for Engineering Team routing
    eng_alerts = [a for a in alerts if a['assigned_team'] == 'Engineering Team']
    if eng_alerts:
        print(f"Routing Success: Found {len(eng_alerts)} alerts assigned to Engineering Team.")
    else:
        print("Routing Failure: No alerts found for Engineering Team.")

if __name__ == "__main__":
    verify()
