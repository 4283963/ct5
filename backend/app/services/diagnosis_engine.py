from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.models.schemas import (
    InefficiencyIssue,
    VoyageDiagnosis,
    OptimizationSuggestion,
    OptimizationPlan,
)
from app.services.metrics_calculator import metrics_calculator


class DiagnosisEngine:
    def diagnose_voyage(
        self, df: pd.DataFrame, voyage_id: str, include_suggestions: bool = True
    ) -> VoyageDiagnosis:
        issues: List[InefficiencyIssue] = []

        issues.extend(self._detect_speed_inefficiencies(df))
        issues.extend(self._detect_fuel_inefficiencies(df))
        issues.extend(self._detect_wind_impact_issues(df))
        issues.extend(self._detect_anomalies(df))
        issues.extend(self._detect_course_deviation(df))

        overall_score = self._calculate_efficiency_score(df, issues)
        total_saving = sum(issue.potential_saving for issue in issues)

        optimization_summary = self._generate_optimization_summary(df, issues)

        return VoyageDiagnosis(
            voyage_id=voyage_id,
            overall_efficiency_score=round(overall_score, 2),
            issues=issues,
            total_potential_saving=round(total_saving, 2),
            optimization_summary=optimization_summary,
        )

    def _detect_speed_inefficiencies(self, df: pd.DataFrame) -> List[InefficiencyIssue]:
        issues: List[InefficiencyIssue] = []

        speed_optimal_low, speed_optimal_high = settings.SPEED_OPTIMAL_RANGE

        too_low_mask = (df["speed"] > 0) & (df["speed"] < speed_optimal_low)
        too_high_mask = df["speed"] > speed_optimal_high

        if too_low_mask.sum() > 0:
            low_speed_fuel = df.loc[too_low_mask, "fuel_consumption"].sum()
            total_fuel = df["fuel_consumption"].sum()
            impact_percent = (low_speed_fuel / total_fuel * 100) if total_fuel > 0 else 0

            worst_idx = df.loc[too_low_mask, "fuel_consumption"].idxmax()
            worst_row = df.loc[worst_idx]

            issues.append(
                InefficiencyIssue(
                    issue_type="speed_too_low",
                    severity="medium" if impact_percent > 10 else "low",
                    description=f"检测到 {too_low_mask.sum()} 个点航速低于最优范围 ({speed_optimal_low} 节)，"
                    f"占总油耗的 {impact_percent:.1f}%",
                    timestamp=worst_row["timestamp"],
                    location={"longitude": float(worst_row["longitude"]), "latitude": float(worst_row["latitude"])},
                    suggested_action=f"建议将航速提升至 {speed_optimal_low}-{speed_optimal_high} 节的经济航速区间",
                    potential_saving=round(low_speed_fuel * 0.15, 2),
                )
            )

        if too_high_mask.sum() > 0:
            high_speed_fuel = df.loc[too_high_mask, "fuel_consumption"].sum()
            total_fuel = df["fuel_consumption"].sum()
            impact_percent = (high_speed_fuel / total_fuel * 100) if total_fuel > 0 else 0

            worst_idx = df.loc[too_high_mask, "fuel_consumption"].idxmax()
            worst_row = df.loc[worst_idx]

            issues.append(
                InefficiencyIssue(
                    issue_type="speed_too_high",
                    severity="high" if impact_percent > 15 else "medium",
                    description=f"检测到 {too_high_mask.sum()} 个点航速高于最优范围 ({speed_optimal_high} 节)，"
                    f"占总油耗的 {impact_percent:.1f}%",
                    timestamp=worst_row["timestamp"],
                    location={"longitude": float(worst_row["longitude"]), "latitude": float(worst_row["latitude"])},
                    suggested_action=f"建议将航速降低至 {speed_optimal_low}-{speed_optimal_high} 节的经济航速区间",
                    potential_saving=round(high_speed_fuel * 0.25, 2),
                )
            )

        return issues

    def _detect_fuel_inefficiencies(self, df: pd.DataFrame) -> List[InefficiencyIssue]:
        issues: List[InefficiencyIssue] = []

        rolling_df = metrics_calculator.calculate_rolling_efficiency(df, window=10)
        efficiency_threshold = rolling_df["rolling_efficiency"].median() * 0.7

        low_eff_mask = (rolling_df["rolling_efficiency"] > 0) & (
            rolling_df["rolling_efficiency"] < efficiency_threshold
        )

        if low_eff_mask.sum() > 0:
            low_eff_fuel = df.loc[low_eff_mask, "fuel_consumption"].sum()
            total_fuel = df["fuel_consumption"].sum()
            impact_percent = (low_eff_fuel / total_fuel * 100) if total_fuel > 0 else 0

            worst_idx = rolling_df.loc[low_eff_mask, "rolling_efficiency"].idxmin()
            worst_row = df.loc[worst_idx]

            issues.append(
                InefficiencyIssue(
                    issue_type="low_fuel_efficiency",
                    severity="high" if impact_percent > 20 else "medium",
                    description=f"检测到 {low_eff_mask.sum()} 个点燃油效率异常偏低，"
                    f"占总油耗的 {impact_percent:.1f}%",
                    timestamp=worst_row["timestamp"],
                    location={"longitude": float(worst_row["longitude"]), "latitude": float(worst_row["latitude"])},
                    suggested_action="检查主机工况、船体附着物情况，考虑调整航行参数",
                    potential_saving=round(low_eff_fuel * 0.2, 2),
                )
            )

        return issues

    def _detect_wind_impact_issues(self, df: pd.DataFrame) -> List[InefficiencyIssue]:
        issues: List[InefficiencyIssue] = []

        wind_impact = metrics_calculator.calculate_wind_impact(df)

        if wind_impact.get("head_wind_penalty", 0) > settings.WIND_IMPACT_THRESHOLD:
            head_wind_fuel = wind_impact["head_wind"]["avg_fuel"] * wind_impact["head_wind"]["count"]
            tail_wind_fuel = wind_impact["tail_wind"]["avg_fuel"] * wind_impact["head_wind"]["count"]
            excess_fuel = head_wind_fuel - tail_wind_fuel

            issues.append(
                InefficiencyIssue(
                    issue_type="high_wind_impact",
                    severity="high",
                    description=f"逆风导致油耗增加 {wind_impact['head_wind_penalty']:.1f}%，"
                    f"建议优化航线或调整航速",
                    suggested_action="考虑绕开强风区域，或根据风向调整航向以减少风阻",
                    potential_saving=round(excess_fuel * 0.4, 2),
                )
            )

        return issues

    def _detect_anomalies(self, df: pd.DataFrame) -> List[InefficiencyIssue]:
        issues: List[InefficiencyIssue] = []

        features = ["speed", "fuel_consumption", "wind_speed", "course"]
        df_features = df[features].copy()

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df_features)

        iso_forest = IsolationForest(contamination=0.02, random_state=42)
        anomaly_labels = iso_forest.fit_predict(scaled_features)

        anomaly_mask = anomaly_labels == -1

        if anomaly_mask.sum() > 0:
            anomaly_df = df[anomaly_mask]
            anomaly_fuel = anomaly_df["fuel_consumption"].sum()

            worst_idx = anomaly_df["fuel_consumption"].idxmax()
            worst_row = df.loc[worst_idx]

            issues.append(
                InefficiencyIssue(
                    issue_type="data_anomaly",
                    severity="low",
                    description=f"检测到 {anomaly_mask.sum()} 个异常数据点，可能影响分析准确性",
                    timestamp=worst_row["timestamp"],
                    location={"longitude": float(worst_row["longitude"]), "latitude": float(worst_row["latitude"])},
                    suggested_action="检查传感器数据采集是否正常，必要时剔除异常点",
                    potential_saving=round(anomaly_fuel * 0.05, 2),
                )
            )

        return issues

    def _detect_course_deviation(self, df: pd.DataFrame) -> List[InefficiencyIssue]:
        issues: List[InefficiencyIssue] = []

        if len(df) < 10:
            return issues

        course_changes = df["course"].diff().abs()
        course_changes = np.minimum(course_changes, 360 - course_changes)

        frequent_turn_mask = course_changes > 30

        if frequent_turn_mask.sum() > len(df) * 0.1:
            turn_fuel = df.loc[frequent_turn_mask, "fuel_consumption"].sum()

            worst_idx = frequent_turn_mask.idxmax()
            worst_row = df.loc[worst_idx]

            issues.append(
                InefficiencyIssue(
                    issue_type="frequent_course_changes",
                    severity="medium",
                    description=f"检测到频繁转向操作 ({frequent_turn_mask.sum()} 次)，可能增加油耗",
                    timestamp=worst_row["timestamp"],
                    location={"longitude": float(worst_row["longitude"]), "latitude": float(worst_row["latitude"])},
                    suggested_action="建议优化航线规划，减少不必要的转向",
                    potential_saving=round(turn_fuel * 0.1, 2),
                )
            )

        return issues

    def _calculate_efficiency_score(
        self, df: pd.DataFrame, issues: List[InefficiencyIssue]
    ) -> float:
        total_fuel = df["fuel_consumption"].sum()
        total_potential_saving = sum(issue.potential_saving for issue in issues)

        base_score = 100.0

        if total_fuel > 0:
            penalty = (total_potential_saving / total_fuel) * 50
            base_score -= min(penalty, 50)

        speed_issues = [i for i in issues if "speed" in i.issue_type]
        fuel_issues = [i for i in issues if "fuel" in i.issue_type]

        for issue in speed_issues:
            if issue.severity == "high":
                base_score -= 10
            elif issue.severity == "medium":
                base_score -= 5

        for issue in fuel_issues:
            if issue.severity == "high":
                base_score -= 15
            elif issue.severity == "medium":
                base_score -= 8

        return max(0, min(100, base_score))

    def _generate_optimization_summary(
        self, df: pd.DataFrame, issues: List[InefficiencyIssue]
    ) -> Dict[str, Any]:
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = {"count": 0, "severity": [], "saving": 0}
            issue_types[issue.issue_type]["count"] += 1
            issue_types[issue.issue_type]["severity"].append(issue.severity)
            issue_types[issue.issue_type]["saving"] += issue.potential_saving

        for key in issue_types:
            issue_types[key]["saving"] = round(issue_types[key]["saving"], 2)

        optimal_speed_info = metrics_calculator.identify_optimal_speed_range(df)
        correlation_info = metrics_calculator.calculate_speed_fuel_correlation(df)

        return {
            "issue_breakdown": issue_types,
            "optimal_speed": optimal_speed_info["optimal_speed"],
            "speed_fuel_correlation": correlation_info["correlation"],
            "total_data_points": len(df),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def generate_optimization_plan(
        self, diagnosis: VoyageDiagnosis, df: pd.DataFrame
    ) -> OptimizationPlan:
        suggestions: List[OptimizationSuggestion] = []

        speed_issues = [i for i in diagnosis.issues if "speed" in i.issue_type]
        fuel_issues = [i for i in diagnosis.issues if "fuel" in i.issue_type]
        wind_issues = [i for i in diagnosis.issues if "wind" in i.issue_type]
        course_issues = [i for i in diagnosis.issues if "course" in i.issue_type]

        if speed_issues:
            total_saving = sum(i.potential_saving for i in speed_issues)
            total_fuel = df["fuel_consumption"].sum()
            saving_percent = (total_saving / total_fuel * 100) if total_fuel > 0 else 0

            suggestions.append(
                OptimizationSuggestion(
                    category="speed_optimization",
                    description=f"优化航速至 {settings.SPEED_OPTIMAL_RANGE[0]}-{settings.SPEED_OPTIMAL_RANGE[1]} 节的经济区间，"
                    f"避免高速航行带来的额外油耗",
                    expected_saving_percent=round(saving_percent, 2),
                    implementation_difficulty="low",
                    priority="high",
                )
            )

        if fuel_issues:
            total_saving = sum(i.potential_saving for i in fuel_issues)
            total_fuel = df["fuel_consumption"].sum()
            saving_percent = (total_saving / total_fuel * 100) if total_fuel > 0 else 0

            suggestions.append(
                OptimizationSuggestion(
                    category="fuel_efficiency",
                    description="进行主机性能检查和船体清洁，维护设备最佳运行状态",
                    expected_saving_percent=round(saving_percent, 2),
                    implementation_difficulty="high",
                    priority="high",
                )
            )

        if wind_issues:
            total_saving = sum(i.potential_saving for i in wind_issues)
            total_fuel = df["fuel_consumption"].sum()
            saving_percent = (total_saving / total_fuel * 100) if total_fuel > 0 else 0

            suggestions.append(
                OptimizationSuggestion(
                    category="weather_routeing",
                    description="引入气象导航系统，根据实时天气预报优化航线选择",
                    expected_saving_percent=round(saving_percent, 2),
                    implementation_difficulty="medium",
                    priority="medium",
                )
            )

        if course_issues:
            total_saving = sum(i.potential_saving for i in course_issues)
            total_fuel = df["fuel_consumption"].sum()
            saving_percent = (total_saving / total_fuel * 100) if total_fuel > 0 else 0

            suggestions.append(
                OptimizationSuggestion(
                    category="route_optimization",
                    description="使用航线规划软件优化航向，减少不必要的转向和绕航",
                    expected_saving_percent=round(saving_percent, 2),
                    implementation_difficulty="medium",
                    priority="medium",
                )
            )

        suggestions.append(
            OptimizationSuggestion(
                category="crew_training",
                description="加强船员节油操作培训，建立经济航行激励机制",
                expected_saving_percent=3.0,
                implementation_difficulty="low",
                priority="low",
            )
        )

        suggestions.sort(key=lambda x: x.expected_saving_percent, reverse=True)

        total_expected_saving = sum(s.expected_saving_percent for s in suggestions)
        baseline_efficiency = diagnosis.overall_efficiency_score
        target_efficiency = min(100, baseline_efficiency + total_expected_saving)

        return OptimizationPlan(
            voyage_id=diagnosis.voyage_id,
            baseline_efficiency=round(baseline_efficiency, 2),
            target_efficiency=round(target_efficiency, 2),
            suggestions=suggestions,
            total_expected_saving=round(total_expected_saving, 2),
            estimated_payback_period="3-6 months" if total_expected_saving > 10 else "6-12 months",
        )

    def batch_diagnose(
        self, voyage_data: Dict[str, pd.DataFrame], include_suggestions: bool = True
    ) -> List[VoyageDiagnosis]:
        diagnoses = []
        for voyage_id, df in voyage_data.items():
            diagnosis = self.diagnose_voyage(df, voyage_id, include_suggestions)
            diagnoses.append(diagnosis)
        return diagnoses


diagnosis_engine = DiagnosisEngine()
