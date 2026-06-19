from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.schemas import (
    VoyageMetrics,
    VoyageSummary,
    VoyageListResponse,
    MetricsComparisonRequest,
    MetricsComparisonResponse,
)
from app.services.data_processor import data_processor
from app.services.metrics_calculator import metrics_calculator

router = APIRouter()


@router.get("/voyages", response_model=VoyageListResponse)
async def list_voyages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        all_voyages = data_processor.get_all_voyages()
        total = len(all_voyages)
        paginated = all_voyages[skip : skip + limit]

        return VoyageListResponse(total=total, voyages=paginated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}", response_model=VoyageSummary)
async def get_voyage_summary(voyage_id: str):
    try:
        all_voyages = data_processor.get_all_voyages()
        voyage = next((v for v in all_voyages if v.voyage_id == voyage_id), None)

        if not voyage:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        return voyage
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}/metrics", response_model=VoyageMetrics)
async def get_voyage_metrics(voyage_id: str, file_id: Optional[str] = None):
    try:
        df = data_processor.get_voyage_data(file_id or "", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        metrics = metrics_calculator.calculate_voyage_metrics(df, voyage_id)
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparison", response_model=MetricsComparisonResponse)
async def compare_voyages(request: MetricsComparisonRequest):
    try:
        voyage_data = {}

        for voyage_id in request.voyage_ids:
            df = data_processor.get_voyage_data("", voyage_id)
            if df is None:
                raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")
            voyage_data[voyage_id] = df

        response = metrics_calculator.calculate_comparison_metrics(
            voyage_data, request.metrics
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}/speed-fuel-correlation")
async def get_speed_fuel_correlation(voyage_id: str):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        correlation = metrics_calculator.calculate_speed_fuel_correlation(df)
        return {"voyage_id": voyage_id, **correlation}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}/wind-impact")
async def get_wind_impact(voyage_id: str):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        wind_impact = metrics_calculator.calculate_wind_impact(df)
        return {"voyage_id": voyage_id, **wind_impact}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}/optimal-speed")
async def get_optimal_speed(voyage_id: str):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        optimal_speed = metrics_calculator.identify_optimal_speed_range(df)
        return {"voyage_id": voyage_id, **optimal_speed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}/rolling-efficiency")
async def get_rolling_efficiency(voyage_id: str, window: int = Query(10, ge=5, le=100)):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        rolling_df = metrics_calculator.calculate_rolling_efficiency(df, window)

        timestamps = rolling_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        efficiency = rolling_df["rolling_efficiency"].fillna(0).tolist()
        distance = rolling_df["cumulative_distance"].fillna(0).tolist()
        fuel = rolling_df["cumulative_fuel"].fillna(0).tolist()

        return {
            "voyage_id": voyage_id,
            "window": window,
            "timestamps": timestamps,
            "rolling_efficiency": [round(v, 2) for v in efficiency],
            "cumulative_distance": [round(v, 2) for v in distance],
            "cumulative_fuel": [round(v, 2) for v in fuel],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyages/{voyage_id}/trajectory")
async def get_voyage_trajectory(voyage_id: str):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        trajectory = []
        for _, row in df.iterrows():
            trajectory.append({
                "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "longitude": float(row["longitude"]),
                "latitude": float(row["latitude"]),
                "speed": float(row["speed"]),
                "fuel_consumption": float(row["fuel_consumption"]),
                "wind_speed": float(row["wind_speed"]),
            })

        return {"voyage_id": voyage_id, "trajectory": trajectory}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
