import re
import io
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np

from app.config import settings
from app.models.schemas import VesselDataPoint, VoyageSummary


class DataProcessor:
    REQUIRED_COLUMNS = [
        "timestamp", "longitude", "latitude", "speed",
        "fuel_consumption", "wind_speed", "wind_direction", "course"
    ]

    COLUMN_MAPPINGS = {
        "时间": "timestamp", "time": "timestamp", "datetime": "timestamp",
        "经度": "longitude", "lon": "longitude", "lng": "longitude",
        "纬度": "latitude", "lat": "latitude",
        "航速": "speed", "speed_knots": "speed", "vessel_speed": "speed",
        "油耗": "fuel_consumption", "fuel": "fuel_consumption", "fuel_rate": "fuel_consumption",
        "风速": "wind_speed", "wind": "wind_speed",
        "风向": "wind_direction",
        "航向": "course", "heading": "course",
        "功率": "engine_power", "主机功率": "engine_power",
        "吃水": "draft", "吃水深度": "draft",
        "船名": "vessel_name", "vessel": "vessel_name",
        "船舶名称": "vessel_name",
        "航次": "voyage_id", "voyage": "voyage_id",
        "出发港": "departure_port", "departure": "departure_port",
        "到达港": "arrival_port", "arrival": "arrival_port",
    }

    def parse_file(self, file_path: Path) -> Tuple[pd.DataFrame, List[str]]:
        suffix = file_path.suffix.lower()

        if suffix in [".csv"]:
            df = pd.read_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif suffix in [".parquet"]:
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        df = self._normalize_columns(df)
        df = self._validate_and_clean(df)
        voyage_ids = self._identify_voyages(df)

        return df, voyage_ids

    def parse_bytes(self, data: bytes, filename: str) -> Tuple[pd.DataFrame, List[str]]:
        suffix = Path(filename).suffix.lower()

        if suffix in [".csv"]:
            df = pd.read_csv(io.BytesIO(data))
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(io.BytesIO(data))
        elif suffix in [".parquet"]:
            df = pd.read_parquet(io.BytesIO(data))
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        df = self._normalize_columns(df)
        df = self._validate_and_clean(df)
        voyage_ids = self._identify_voyages(df)

        return df, voyage_ids

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df.columns = [str(col).strip().lower() for col in df.columns]

        rename_map = {}
        for col in df.columns:
            if col in self.COLUMN_MAPPINGS:
                rename_map[col] = self.COLUMN_MAPPINGS[col]

        if rename_map:
            df = df.rename(columns=rename_map)

        return df

    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Available columns: {list(df.columns)}"
            )

        df = df.copy()

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])

        df = df.sort_values("timestamp").reset_index(drop=True)

        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df = df[(df["longitude"].between(-180, 180)) & (df["latitude"].between(-90, 90))]

        for col in ["speed", "fuel_consumption", "wind_speed", "wind_direction", "course"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[(df["speed"].between(0, 40)) & (df["fuel_consumption"] >= 0)]

        for col in ["engine_power", "draft"]:
            if col not in df.columns:
                df[col] = None
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in ["vessel_name", "departure_port", "arrival_port", "voyage_id"]:
            if col not in df.columns:
                df[col] = None
            else:
                df[col] = df[col].astype(str).fillna("")

        df = df.dropna(subset=["longitude", "latitude", "speed", "fuel_consumption"])

        df = self._remove_outliers(df)

        return df.reset_index(drop=True)

    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["speed", "fuel_consumption", "wind_speed"]:
            if col in df.columns:
                q1 = df[col].quantile(0.01)
                q3 = df[col].quantile(0.99)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

        return df

    def _identify_voyages(self, df: pd.DataFrame) -> List[str]:
        if "voyage_id" in df.columns and df["voyage_id"].notna().any():
            voyage_ids = df["voyage_id"].dropna().unique().tolist()
            if len(voyage_ids) > 0 and voyage_ids[0]:
                return [str(vid) for vid in voyage_ids]

        time_gaps = df["timestamp"].diff().dt.total_seconds()
        gap_threshold = 3600 * 6

        voyage_markers = (time_gaps > gap_threshold) | (df.index == 0)
        voyage_ids = []

        for i, is_start in enumerate(voyage_markers):
            if is_start:
                voyage_id = f"VOYAGE_{len(voyage_ids) + 1:04d}"
                df.loc[df.index[i:], "voyage_id"] = voyage_id

        return df["voyage_id"].unique().tolist()

    def save_processed_data(self, df: pd.DataFrame, file_id: str) -> List[str]:
        voyage_ids = df["voyage_id"].unique().tolist()

        for voyage_id in voyage_ids:
            voyage_df = df[df["voyage_id"] == voyage_id].copy()
            output_path = settings.PROCESSED_DIR / f"{file_id}_{voyage_id}.parquet"
            voyage_df.to_parquet(output_path, index=False)

        return voyage_ids

    def get_voyage_data(self, file_id: str, voyage_id: str) -> Optional[pd.DataFrame]:
        file_path = settings.PROCESSED_DIR / f"{file_id}_{voyage_id}.parquet"
        if not file_path.exists():
            all_files = list(settings.PROCESSED_DIR.glob(f"*_{voyage_id}.parquet"))
            if all_files:
                file_path = all_files[0]
            else:
                return None

        return pd.read_parquet(file_path)

    def get_all_voyages(self) -> List[VoyageSummary]:
        voyage_files = list(settings.PROCESSED_DIR.glob("*.parquet"))
        voyages = []

        for file_path in voyage_files:
            try:
                df = pd.read_parquet(file_path)
                summary = self._compute_voyage_summary(df, file_path.stem)
                voyages.append(summary)
            except Exception:
                continue

        return sorted(voyages, key=lambda x: x.start_time, reverse=True)

    def _compute_voyage_summary(self, df: pd.DataFrame, voyage_stem: str) -> VoyageSummary:
        parts = voyage_stem.split("_", 1)
        file_id = parts[0] if len(parts) > 1 else ""
        voyage_id = df["voyage_id"].iloc[0] if "voyage_id" in df.columns else voyage_stem

        total_distance = self._calculate_total_distance(df)
        total_fuel = df["fuel_consumption"].sum()

        time_diff = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds() / 3600
        avg_speed = df["speed"].mean() if time_diff > 0 else 0

        fuel_efficiency = (total_fuel / total_distance * 1000) if total_distance > 0 else 0

        vessel_name = df["vessel_name"].iloc[0] if "vessel_name" in df.columns else "Unknown"
        departure_port = df["departure_port"].iloc[0] if "departure_port" in df.columns else "Unknown"
        arrival_port = df["arrival_port"].iloc[-1] if "arrival_port" in df.columns else "Unknown"

        return VoyageSummary(
            voyage_id=voyage_id,
            vessel_name=str(vessel_name),
            departure_port=str(departure_port),
            arrival_port=str(arrival_port),
            start_time=df["timestamp"].iloc[0],
            end_time=df["timestamp"].iloc[-1],
            total_distance=round(total_distance, 2),
            total_fuel=round(total_fuel, 2),
            avg_speed=round(avg_speed, 2),
            fuel_efficiency=round(fuel_efficiency, 2)
        )

    def _calculate_total_distance(self, df: pd.DataFrame) -> float:
        if len(df) < 2:
            return 0.0

        lons = df["longitude"].values
        lats = df["latitude"].values

        lon1, lat1 = np.radians(lons[:-1]), np.radians(lats[:-1])
        lon2, lat2 = np.radians(lons[1:]), np.radians(lats[1:])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        earth_radius = 6371.0
        distances = c * earth_radius

        return float(np.sum(distances))


data_processor = DataProcessor()
