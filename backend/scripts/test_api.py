#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app


def main():
    client = TestClient(app)

    print("Testing API endpoints...")
    print("=" * 60)

    # Health check
    resp = client.get("/api/health")
    print(f"\nHealth: {resp.json()}")

    # Upload module endpoints
    print("\n1. Upload module:")
    resp = client.get("/api/upload/files")
    print(f"   GET /api/upload/files - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Files: {len(data)}")

    # Metrics module endpoints
    print("\n2. Metrics module:")

    resp = client.get("/api/metrics/voyages")
    print(f"   GET /api/metrics/voyages - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Total voyages: {data.get('total')}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001 - {resp.status_code}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001/metrics")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001/metrics - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Speed data points: {len(data.get('speed_data', []))}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001/speed-fuel-correlation")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001/speed-fuel-correlation - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Correlation: {data.get('correlation')}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001/wind-impact")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001/wind-impact - {resp.status_code}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001/optimal-speed")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001/optimal-speed - {resp.status_code}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001/trajectory")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001/trajectory - {resp.status_code}")

    resp = client.get("/api/metrics/voyages/VOYAGE_0001/rolling-efficiency")
    print(f"   GET /api/metrics/voyages/VOYAGE_0001/rolling-efficiency - {resp.status_code}")

    resp = client.post("/api/metrics/comparison", json={
        "voyage_ids": ["VOYAGE_0001", "VOYAGE_0002"],
        "metrics": ["speed", "fuel_consumption", "wind_speed"]
    })
    print(f"   POST /api/metrics/comparison - {resp.status_code}")

    # Diagnosis module endpoints
    print("\n3. Diagnosis module:")

    resp = client.get("/api/diagnosis/voyage/VOYAGE_0001")
    print(f"   GET /api/diagnosis/voyage/VOYAGE_0001 - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Score: {data.get('overall_efficiency_score')}")
        print(f"     Issues: {len(data.get('issues', []))}")

    resp = client.get("/api/diagnosis/voyage/VOYAGE_0001/optimization-plan")
    print(f"   GET /api/diagnosis/voyage/VOYAGE_0001/optimization-plan - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Suggestions: {len(data.get('suggestions', []))}")

    resp = client.get("/api/diagnosis/voyage/VOYAGE_0001/issues")
    print(f"   GET /api/diagnosis/voyage/VOYAGE_0001/issues - {resp.status_code}")

    resp = client.get("/api/diagnosis/ranking")
    print(f"   GET /api/diagnosis/ranking - {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"     Ranked voyages: {len(data.get('ranking', []))}")

    resp = client.get("/api/diagnosis/statistics")
    print(f"   GET /api/diagnosis/statistics - {resp.status_code}")

    resp = client.post("/api/diagnosis/batch", json={
        "voyage_ids": ["VOYAGE_0001", "VOYAGE_0002"],
        "include_suggestions": True
    })
    print(f"   POST /api/diagnosis/batch - {resp.status_code}")

    print("\n" + "=" * 60)
    print("API endpoint test completed!")


if __name__ == "__main__":
    main()
