#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from pathlib import Path
from app.services.data_processor import data_processor
from app.config import settings


def main():
    print("Processing sample data into processed directory...")
    print("=" * 50)

    sample_dir = settings.SAMPLE_DIR
    sample_files = list(sample_dir.glob("*.csv"))

    total_records = 0
    total_voyages = 0

    for sample_file in sample_files:
        print(f"\nProcessing: {sample_file.name}")
        try:
            df, errors = data_processor.parse_file(sample_file)
            voyage_ids = data_processor.save_processed_data(df, "sample")

            print(f"  Records: {len(df)}")
            print(f"  Voyages: {voyage_ids}")
            print(f"  Errors: {len(errors)}")

            total_records += len(df)
            total_voyages += len(voyage_ids)
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 50)
    print(f"Total records processed: {total_records}")
    print(f"Total voyages: {total_voyages}")

    all_voyages = data_processor.get_all_voyages()
    print(f"Voyages in processed dir: {len(all_voyages)}")
    for v in all_voyages:
        print(f"  - {v.voyage_id}: {v.vessel_name} ({v.departure_port} -> {v.arrival_port})")


if __name__ == "__main__":
    main()
