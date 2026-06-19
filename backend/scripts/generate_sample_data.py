#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def generate_voyage_data(
    vessel_name: str,
    voyage_id: str,
    departure_port: str,
    arrival_port: str,
    start_date: datetime,
    duration_hours: int = 72,
    interval_minutes: int = 10
) -> pd.DataFrame:
    num_points = int(duration_hours * 60 / interval_minutes)
    timestamps = [start_date + timedelta(minutes=i * interval_minutes) for i in range(num_points)]

    base_lon = np.random.uniform(110, 130)
    base_lat = np.random.uniform(20, 35)

    progress = np.linspace(0, 1, num_points)
    lon = base_lon + progress * np.random.uniform(10, 25) + np.sin(progress * 4) * 2
    lat = base_lat + progress * np.random.uniform(-10, 10) + np.cos(progress * 3) * 1.5

    base_speed = np.random.uniform(13, 17)
    speed = base_speed + np.sin(progress * 6) * 2 + np.random.normal(0, 0.5, num_points)
    speed = np.clip(speed, 8, 22)

    base_fuel = 25 + (base_speed - 14) * 1.8
    fuel = base_fuel + (speed - base_speed) * 2.5 + np.random.normal(0, 1.5, num_points)
    fuel = np.clip(fuel, 15, 50)

    abnormal_mask = np.random.choice([False, True], num_points, p=[0.95, 0.05])
    fuel[abnormal_mask] *= np.random.uniform(1.3, 1.8, abnormal_mask.sum())
    speed[abnormal_mask] *= np.random.uniform(0.7, 1.4, abnormal_mask.sum())

    wind_speed = np.random.uniform(3, 20, num_points)
    wind_direction = np.random.uniform(0, 360, num_points)
    base_course = np.random.uniform(60, 120)
    course = base_course + np.sin(progress * 8) * 15 + np.random.normal(0, 5, num_points)
    course = (course + 360) % 360

    frequent_turn_mask = np.random.choice([False, True], num_points, p=[0.9, 0.1])
    course[frequent_turn_mask] += np.random.uniform(-45, 45, frequent_turn_mask.sum())
    course[frequent_turn_mask] = (course[frequent_turn_mask] + 360) % 360

    df = pd.DataFrame({
        'timestamp': timestamps,
        'longitude': lon.round(6),
        'latitude': lat.round(6),
        'speed': speed.round(2),
        'fuel_consumption': fuel.round(2),
        'wind_speed': wind_speed.round(2),
        'wind_direction': wind_direction.round(2),
        'course': course.round(2),
        'engine_power': (fuel * 30 + np.random.normal(0, 50, num_points)).round(1),
        'draft': np.random.uniform(10, 14),
        'vessel_name': vessel_name,
        'voyage_id': voyage_id,
        'departure_port': departure_port,
        'arrival_port': arrival_port
    })

    return df


def main():
    output_dir = Path(__file__).parent.parent / 'data' / 'sample'
    output_dir.mkdir(parents=True, exist_ok=True)

    voyages = [
        {
            'vessel_name': '远洋一号',
            'voyage_id': 'VOYAGE_0001',
            'departure_port': '上海',
            'arrival_port': '新加坡',
            'start_date': datetime(2024, 1, 1),
            'duration_hours': 120
        },
        {
            'vessel_name': '远洋一号',
            'voyage_id': 'VOYAGE_0002',
            'departure_port': '新加坡',
            'arrival_port': '鹿特丹',
            'start_date': datetime(2024, 1, 8),
            'duration_hours': 240
        },
        {
            'vessel_name': '远洋二号',
            'voyage_id': 'VOYAGE_0003',
            'departure_port': '宁波',
            'arrival_port': '洛杉矶',
            'start_date': datetime(2024, 1, 5),
            'duration_hours': 288
        },
        {
            'vessel_name': '远洋三号',
            'voyage_id': 'VOYAGE_0004',
            'departure_port': '深圳',
            'arrival_port': '悉尼',
            'start_date': datetime(2024, 1, 10),
            'duration_hours': 168
        },
        {
            'vessel_name': '远洋二号',
            'voyage_id': 'VOYAGE_0005',
            'departure_port': '洛杉矶',
            'arrival_port': '上海',
            'start_date': datetime(2024, 1, 20),
            'duration_hours': 264
        }
    ]

    all_data = []
    for voyage in voyages:
        print(f"Generating data for {voyage['voyage_id']}: {voyage['departure_port']} -> {voyage['arrival_port']}")
        df = generate_voyage_data(**voyage)
        all_data.append(df)

        voyage_csv = output_dir / f"{voyage['voyage_id']}.csv"
        df.to_csv(voyage_csv, index=False)
        print(f"  Saved to {voyage_csv.name} ({len(df)} records)")

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_csv = output_dir / 'combined_voyages.csv'
    combined_df.to_csv(combined_csv, index=False)
    print(f"\nCombined data saved to {combined_csv.name} ({len(combined_df)} total records)")

    combined_parquet = output_dir / 'combined_voyages.parquet'
    combined_df.to_parquet(combined_parquet, index=False)
    print(f"Parquet version saved to {combined_parquet.name}")

    print("\nDone! Sample data generated successfully.")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()
