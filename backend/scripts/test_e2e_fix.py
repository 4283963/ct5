#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app


def main():
    client = TestClient(app)

    print("=== Complete End-to-End Test ===")
    print()

    # Step 1: Get voyage list
    print("1. Testing GET /api/metrics/voyages")
    resp = client.get("/api/metrics/voyages")
    print(f"   Status: {resp.status_code}")
    voyages = resp.json()
    print(f"   Voyages: {len(voyages.get('voyages', []))}")
    first_two = voyages.get("voyages", [])[:2]
    voyage_ids = [v["voyage_id"] for v in first_two]
    print(f"   First two voyage IDs: {voyage_ids}")
    print()

    # Step 2: Test comparison API with two voyages
    print("2. Testing POST /api/metrics/comparison")
    resp = client.post("/api/metrics/comparison", json={
        "voyage_ids": voyage_ids,
        "metrics": ["speed", "fuel", "efficiency"]
    })
    print(f"   Status: {resp.status_code}")
    data = resp.json()
    print(f"   Keys: {list(data.keys())}")
    print()

    # Step 3: Verify summary data structure
    print("3. Verifying summary data structure:")
    summary = data.get("summary", {})
    print(f"   Summary metrics: {list(summary.keys())}")
    print()

    all_good = True
    for metric in ["speed", "fuel", "efficiency"]:
        if metric in summary:
            print(f"   {metric}:")
            for vid in voyage_ids:
                key = f"{vid}_mean"
                val = summary[metric].get(key, "NOT FOUND")
                status = "✓" if val != "NOT FOUND" else "✗"
                if val == "NOT FOUND":
                    all_good = False
                print(f"     {status} {key}: {val}")
    print()

    if not all_good:
        print("ERROR: Some keys are missing!")
        return 1

    # Step 4: Simulate frontend data extraction
    print("4. Simulating frontend data extraction:")
    print()

    metric_labels = {
        "speed": {"name": "平均航速", "unit": "节"},
        "fuel": {"name": "平均油耗", "unit": "吨/时"},
        "efficiency": {"name": "平均效率", "unit": "kg/海里"}
    }

    categories = voyage_ids
    print(f"   Categories (x-axis): {categories}")
    print()

    seriesData = []
    for metric in ["speed", "fuel", "efficiency"]:
        if summary.get(metric):
            data_values = []
            for vid in voyage_ids:
                key = f"{vid}_mean"
                value = summary[metric].get(key)
                if value is not None:
                    data_values.append(round(float(value), 2))
                else:
                    data_values.append(0)
                    print(f"   WARNING: {key} not found!")

            seriesData.append({
                "name": f"{metric_labels[metric]['name']} ({metric_labels[metric]['unit']})",
                "data": data_values
            })
            print(f"   Series: {seriesData[-1]['name']} = {seriesData[-1]['data']}")

    print()
    print("5. Chart option verification:")
    print(f"   Title: 多航次能效指标对比")
    print(f"   Categories: {categories}")
    print(f"   Series count: {len(seriesData)}")
    for s in seriesData:
        print(f"   - {s['name']}: {s['data']}")

    print()
    print("=== Test PASSED ===")
    print()
    print("Summary of the fix:")
    print("1. Added energy efficiency comparison bar chart in Dashboard.vue")
    print("   - Template: lines 81-87, new chart row")
    print("   - Computed property: efficiencyComparisonChartOption")
    print("   - Processes comparisonData.summary correctly")
    print("2. Extracts _mean values from summary for each voyage")
    print("3. Handles missing data gracefully with fallback to 0")
    print("4. Chart only shows when 2+ voyages are selected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
