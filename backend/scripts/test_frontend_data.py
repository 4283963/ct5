#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

print("Testing comparison API data format for frontend...")
print("=" * 60)

resp = client.post('/api/metrics/comparison', json={
    'voyage_ids': ['VOYAGE_0001', 'VOYAGE_0002'],
    'metrics': ['speed', 'fuel', 'efficiency']
})

print(f"Status: {resp.status_code}")
data = resp.json()

print("\nChecking data structure:")
print(f"  - Has 'voyage_ids': {'voyage_ids' in data}")
print(f"  - Has 'metrics': {'metrics' in data}")
print(f"  - Has 'summary': {'summary' in data}")

if 'summary' in data:
    summary = data['summary']
    print(f"\nSummary keys: {list(summary.keys())}")
    
    for metric in ['speed', 'fuel', 'efficiency']:
        if metric in summary:
            print(f"\n  {metric}:")
            for key, value in summary[metric].items():
                print(f"    {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Simulating frontend data extraction:")
    
    voyage_ids = ['VOYAGE_0001', 'VOYAGE_0002']
    metric_labels = {
        'speed': {'name': '平均航速', 'unit': '节'},
        'fuel': {'name': '平均油耗', 'unit': '吨/时'},
        'efficiency': {'name': '平均效率', 'unit': 'kg/海里'}
    }
    
    for metric in ['speed', 'fuel', 'efficiency']:
        if metric in summary:
            print(f"\n  {metric_labels[metric]['name']}:")
            for voyage_id in voyage_ids:
                key = f"{voyage_id}_mean"
                value = summary[metric].get(key)
                if value is not None:
                    formatted = round(float(value), 2)
                    print(f"    {voyage_id}: {formatted} {metric_labels[metric]['unit']}")
                else:
                    print(f"    {voyage_id}: KEY NOT FOUND!")

print("\n" + "=" * 60)
print("Data format test completed!")
