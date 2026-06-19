from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats

from app.config import settings
from app.models.schemas import (
    MetricDataPoint,
    VoyageMetrics,
    MetricsComparisonResponse,
    CarbonEmissionResponse,
    FuelTypeInfo,
    FuelTypesResponse,
)


class MetricsCalculator:
    def calculate_voyage_metrics(self, df: pd.DataFrame, voyage_id: str) -> VoyageMetrics:
        timestamps = df["timestamp"].tolist()

        speed_data = self._create_metric_series(timestamps, df["speed"].tolist())
        fuel_data = self._create_metric_series(timestamps, df["fuel_consumption"].tolist())
        wind_data = self._create_metric_series(timestamps, df["wind_speed"].tolist())

        efficiency = self._calculate_efficiency_series(df)
        efficiency_data = self._create_metric_series(timestamps, efficiency)

        return VoyageMetrics(
            voyage_id=voyage_id,
            speed_data=speed_data,
            fuel_data=fuel_data,
            wind_data=wind_data,
            efficiency_data=efficiency_data,
        )

    def _create_metric_series(
        self, timestamps: List[datetime], values: List[float]
    ) -> List[MetricDataPoint]:
        return [
            MetricDataPoint(timestamp=ts, value=round(v, 2))
            for ts, v in zip(timestamps, values)
        ]

    def _calculate_efficiency_series(self, df: pd.DataFrame) -> List[float]:
        distances = self._calculate_segment_distances(df)

        efficiency = []
        for i in range(len(df)):
            if i == 0:
                efficiency.append(0.0)
            else:
                fuel = df["fuel_consumption"].iloc[i]
                dist = distances[i - 1] if i - 1 < len(distances) else 0
                if dist > 0 and fuel > 0:
                    eff = (dist / fuel) * 1000
                else:
                    eff = 0.0
                efficiency.append(round(eff, 2))

        return efficiency

    def _calculate_segment_distances(self, df: pd.DataFrame) -> np.ndarray:
        if len(df) < 2:
            return np.array([])

        lons = df["longitude"].values
        lats = df["latitude"].values

        lon1, lat1 = np.radians(lons[:-1]), np.radians(lats[:-1])
        lon2, lat2 = np.radians(lons[1:]), np.radians(lats[1:])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        earth_radius = 6371.0
        return c * earth_radius

    def calculate_comparison_metrics(
        self, voyage_data: Dict[str, pd.DataFrame], metrics_to_include: List[str]
    ) -> MetricsComparisonResponse:
        voyage_ids = list(voyage_data.keys())

        metrics_data: Dict[str, Dict[str, List[MetricDataPoint]]] = {}
        summary_stats: Dict[str, Dict[str, float]] = {}

        for metric in metrics_to_include:
            metrics_data[metric] = {}
            summary_stats[metric] = {}

            for voyage_id, df in voyage_data.items():
                timestamps = df["timestamp"].tolist()

                if metric == "speed":
                    values = df["speed"].tolist()
                elif metric == "fuel":
                    values = df["fuel_consumption"].tolist()
                elif metric == "wind":
                    values = df["wind_speed"].tolist()
                elif metric == "efficiency":
                    values = self._calculate_efficiency_series(df)
                else:
                    values = [0.0] * len(timestamps)

                metrics_data[metric][voyage_id] = self._create_metric_series(timestamps, values)

                stats_dict = self._calculate_statistics(values)
                for key, value in stats_dict.items():
                    summary_stats[metric][f"{voyage_id}_{key}"] = value

        return MetricsComparisonResponse(
            voyage_ids=voyage_ids,
            metrics=metrics_data,
            summary=summary_stats,
        )

    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        valid_values = [v for v in values if v is not None and not np.isnan(v) and v > 0]

        if not valid_values:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p25": 0.0,
                "p75": 0.0,
            }

        arr = np.array(valid_values)

        return {
            "mean": round(float(np.mean(arr)), 2),
            "median": round(float(np.median(arr)), 2),
            "std": round(float(np.std(arr)), 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
            "p25": round(float(np.percentile(arr, 25)), 2),
            "p75": round(float(np.percentile(arr, 75)), 2),
        }

    def calculate_speed_fuel_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        speed = df["speed"].values
        fuel = df["fuel_consumption"].values

        mask = (speed > 0) & (fuel > 0)
        speed_clean = speed[mask]
        fuel_clean = fuel[mask]

        if len(speed_clean) < 2:
            return {"correlation": 0.0, "p_value": 1.0, "equation": "y = 0", "r_squared": 0.0}

        correlation, p_value = stats.pearsonr(speed_clean, fuel_clean)

        z = np.polyfit(speed_clean, fuel_clean, 2)
        p = np.poly1d(z)

        y_pred = p(speed_clean)
        ss_res = np.sum((fuel_clean - y_pred) ** 2)
        ss_tot = np.sum((fuel_clean - np.mean(fuel_clean)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "correlation": round(float(correlation), 4),
            "p_value": round(float(p_value), 4),
            "equation": f"y = {z[0]:.4f}x² + {z[1]:.4f}x + {z[2]:.4f}",
            "r_squared": round(float(r_squared), 4),
        }

    def calculate_wind_impact(self, df: pd.DataFrame) -> Dict[str, Any]:
        wind_speed = df["wind_speed"].values
        wind_direction = df["wind_direction"].values
        course = df["course"].values
        speed = df["speed"].values
        fuel = df["fuel_consumption"].values

        wind_course_diff = np.abs(wind_direction - course)
        wind_course_diff = np.minimum(wind_course_diff, 360 - wind_course_diff)

        head_wind_mask = wind_course_diff < 90
        tail_wind_mask = wind_course_diff > 270
        cross_wind_mask = (wind_course_diff >= 90) & (wind_course_diff <= 270)

        def get_segment_stats(mask):
            seg_fuel = fuel[mask]
            seg_speed = speed[mask]
            seg_wind = wind_speed[mask]

            if len(seg_fuel) < 2:
                return {"avg_fuel": 0.0, "avg_speed": 0.0, "avg_wind": 0.0, "count": 0}

            return {
                "avg_fuel": round(float(np.mean(seg_fuel)), 2),
                "avg_speed": round(float(np.mean(seg_speed)), 2),
                "avg_wind": round(float(np.mean(seg_wind)), 2),
                "count": int(np.sum(mask)),
            }

        results = {
            "head_wind": get_segment_stats(head_wind_mask),
            "tail_wind": get_segment_stats(tail_wind_mask),
            "cross_wind": get_segment_stats(cross_wind_mask),
        }

        base_fuel = results["tail_wind"]["avg_fuel"]
        if base_fuel > 0:
            results["head_wind_penalty"] = round(
                ((results["head_wind"]["avg_fuel"] - base_fuel) / base_fuel) * 100, 2
            )
        else:
            results["head_wind_penalty"] = 0.0

        return results

    def calculate_rolling_efficiency(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        df = df.copy()
        df["distance_segment"] = np.concatenate([[0], self._calculate_segment_distances(df)])
        df["cumulative_distance"] = df["distance_segment"].cumsum()
        df["cumulative_fuel"] = df["fuel_consumption"].cumsum()

        df["rolling_distance"] = df["distance_segment"].rolling(window=window).sum()
        df["rolling_fuel"] = df["fuel_consumption"].rolling(window=window).sum()

        df["rolling_efficiency"] = np.where(
            df["rolling_fuel"] > 0,
            (df["rolling_distance"] / df["rolling_fuel"]) * 1000,
            0,
        )

        return df

    def identify_optimal_speed_range(self, df: pd.DataFrame) -> Dict[str, Any]:
        speed = df["speed"].values
        fuel = df["fuel_consumption"].values

        mask = (speed > 0) & (fuel > 0)
        speed_clean = speed[mask]
        fuel_clean = fuel[mask]

        if len(speed_clean) < 10:
            return {
                "optimal_speed": settings.SPEED_OPTIMAL_RANGE[0],
                "optimal_range": settings.SPEED_OPTIMAL_RANGE,
                "efficiency_at_optimal": 0.0,
                "speed_bins": [],
                "efficiency_by_speed": [],
            }

        fuel_per_distance = fuel_clean / speed_clean

        speed_bins = np.linspace(speed_clean.min(), speed_clean.max(), 10)
        bin_indices = np.digitize(speed_clean, speed_bins)

        efficiency_by_bin = []
        for i in range(1, len(speed_bins)):
            bin_mask = bin_indices == i
            if np.sum(bin_mask) > 0:
                avg_eff = np.mean(1 / fuel_per_distance[bin_mask])
                efficiency_by_bin.append(
                    {
                        "speed_bin": round(float((speed_bins[i - 1] + speed_bins[i]) / 2), 2),
                        "avg_efficiency": round(float(avg_eff), 2),
                        "count": int(np.sum(bin_mask)),
                    }
                )

        max_eff_idx = np.argmax([e["avg_efficiency"] for e in efficiency_by_bin])
        optimal_speed = efficiency_by_bin[max_eff_idx]["speed_bin"]

        return {
            "optimal_speed": optimal_speed,
            "optimal_range": (
                round(optimal_speed - 1, 2),
                round(optimal_speed + 1, 2),
            ),
            "efficiency_at_optimal": efficiency_by_bin[max_eff_idx]["avg_efficiency"],
            "speed_bins": speed_bins.tolist(),
            "efficiency_by_speed": efficiency_by_bin,
        }

    def get_available_fuel_types(self) -> FuelTypesResponse:
        fuel_types = []
        for code, info in settings.FUEL_TYPES.items():
            fuel_types.append(
                FuelTypeInfo(
                    code=code,
                    name=info["name"],
                    carbon_factor=info["carbon_factor"],
                    density=info["density"],
                    sulfur_content=info["sulfur_content"],
                )
            )
        return FuelTypesResponse(fuel_types=fuel_types)

    def calculate_carbon_emission(
        self,
        distance: float,
        avg_speed: float,
        fuel_type: str,
        reference_df: Optional[pd.DataFrame] = None,
    ) -> CarbonEmissionResponse:
        if fuel_type not in settings.FUEL_TYPES:
            raise ValueError(f"Unknown fuel type: {fuel_type}")

        fuel_info = settings.FUEL_TYPES[fuel_type]
        carbon_factor = fuel_info["carbon_factor"]
        sulfur_content = fuel_info["sulfur_content"]

        if reference_df is not None and len(reference_df) > 0:
            total_distance_ref = self._calculate_total_distance(reference_df)
            total_fuel_ref = reference_df["fuel_consumption"].sum()
            if total_distance_ref > 0 and total_fuel_ref > 0:
                efficiency_coeff = total_distance_ref / total_fuel_ref
            else:
                efficiency_coeff = settings.DEFAULT_FUEL_CONSUMPTION_RATE
        else:
            efficiency_coeff = settings.DEFAULT_FUEL_CONSUMPTION_RATE

        efficiency_coeff = max(1.0, efficiency_coeff)
        total_fuel_consumption = distance / efficiency_coeff
        total_fuel_consumption = max(0.0, total_fuel_consumption)

        base_carbon = total_fuel_consumption * carbon_factor
        speed_penalty = self._calculate_speed_penalty(avg_speed)
        total_carbon_emission = base_carbon * (1 + speed_penalty)

        sulfur_emission = total_fuel_consumption * sulfur_content

        duration_hours = distance / avg_speed if avg_speed > 0 else 0

        if efficiency_coeff >= 200:
            efficiency_level = "excellent"
        elif efficiency_coeff >= 100:
            efficiency_level = "good"
        elif efficiency_coeff >= 50:
            efficiency_level = "fair"
        else:
            efficiency_level = "poor"

        recommendations = self._generate_emission_recommendations(
            efficiency_coeff, avg_speed, fuel_type, total_carbon_emission
        )

        emission_breakdown = {
            "base_carbon": round(base_carbon, 2),
            "speed_penalty_carbon": round(total_carbon_emission - base_carbon, 2),
            "co2_equivalent": round(total_carbon_emission * 3.664, 2),
            "trees_needed": round(total_carbon_emission / 21.77, 1),
            "cars_equivalent": round(total_carbon_emission / 4.6, 1),
        }

        return CarbonEmissionResponse(
            total_carbon_emission=round(total_carbon_emission, 2),
            total_fuel_consumption=round(total_fuel_consumption, 2),
            fuel_type=fuel_type,
            fuel_type_name=fuel_info["name"],
            distance=round(distance, 2),
            avg_speed=round(avg_speed, 2),
            duration_hours=round(duration_hours, 2),
            efficiency_coefficient=round(efficiency_coeff, 2),
            carbon_factor=carbon_factor,
            sulfur_emission=round(sulfur_emission, 4),
            emission_breakdown=emission_breakdown,
            efficiency_level=efficiency_level,
            recommendations=recommendations,
        )

    def _calculate_total_distance(self, df: pd.DataFrame) -> float:
        distances = self._calculate_segment_distances(df)
        return float(np.sum(distances)) if len(distances) > 0 else 0.0

    def _calculate_speed_penalty(self, avg_speed: float) -> float:
        opt_low, opt_high = settings.SPEED_OPTIMAL_RANGE
        if avg_speed < opt_low:
            return (opt_low - avg_speed) * 0.01
        elif avg_speed > opt_high:
            return (avg_speed - opt_high) * 0.03
        return 0.0

    def _generate_emission_recommendations(
        self,
        efficiency_coeff: float,
        avg_speed: float,
        fuel_type: str,
        total_carbon: float,
    ) -> List[str]:
        recommendations = []

        opt_low, opt_high = settings.SPEED_OPTIMAL_RANGE
        if avg_speed > opt_high:
            recommendations.append(
                f"当前航速 {avg_speed:.1f} 节高于最优区间 ({opt_low}-{opt_high} 节)，"
                f"建议减速至经济航速以降低碳排放"
            )
        elif avg_speed < opt_low:
            recommendations.append(
                f"当前航速 {avg_speed:.1f} 节较低，可适当调整航速以平衡时效与燃油效率"
            )
        else:
            recommendations.append(
                f"当前航速 {avg_speed:.1f} 节处于最优区间，保持该航速可获得最佳能效"
            )

        if fuel_type in ["HFO"]:
            recommendations.append(
                "当前使用重油，碳排放较高，建议考虑切换至低硫燃油(VLSFO)或LNG以减少排放"
            )
        elif fuel_type == "LNG":
            recommendations.append(
                "当前使用LNG作为燃料，碳排放已处于较低水平，符合环保趋势"
            )

        if efficiency_coeff < 50:
            recommendations.append(
                "能效系数偏低，建议参考历史高效航次的运营参数进行优化调整"
            )
        elif efficiency_coeff >= 200:
            recommendations.append(
                "能效系数优秀，当前运营模式可作为标准参考"
            )

        if total_carbon > 50:
            recommendations.append(
                "预计碳排放量较大，建议通过气象导航优化航线以进一步降低排放"
            )

        return recommendations


metrics_calculator = MetricsCalculator()
