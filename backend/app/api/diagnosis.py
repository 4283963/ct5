from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import (
    VoyageDiagnosis,
    DiagnosisRequest,
    BatchDiagnosisRequest,
    OptimizationPlan,
)
from app.services.data_processor import data_processor
from app.services.diagnosis_engine import diagnosis_engine

router = APIRouter()


@router.post("/voyage", response_model=VoyageDiagnosis)
async def diagnose_voyage(request: DiagnosisRequest):
    try:
        df = data_processor.get_voyage_data("", request.voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {request.voyage_id} not found")

        diagnosis = diagnosis_engine.diagnose_voyage(
            df, request.voyage_id, request.include_suggestions
        )
        return diagnosis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyage/{voyage_id}", response_model=VoyageDiagnosis)
async def get_voyage_diagnosis(voyage_id: str, include_suggestions: bool = True):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        diagnosis = diagnosis_engine.diagnose_voyage(df, voyage_id, include_suggestions)
        return diagnosis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[VoyageDiagnosis])
async def batch_diagnose(request: BatchDiagnosisRequest):
    try:
        voyage_data = {}

        for voyage_id in request.voyage_ids:
            df = data_processor.get_voyage_data("", voyage_id)
            if df is None:
                raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")
            voyage_data[voyage_id] = df

        diagnoses = diagnosis_engine.batch_diagnose(voyage_data, request.include_suggestions)
        return diagnoses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyage/{voyage_id}/optimization-plan", response_model=OptimizationPlan)
async def get_optimization_plan(voyage_id: str):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        diagnosis = diagnosis_engine.diagnose_voyage(df, voyage_id, True)
        plan = diagnosis_engine.generate_optimization_plan(diagnosis, df)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voyage/{voyage_id}/issues")
async def get_voyage_issues(voyage_id: str, severity: str = None):
    try:
        df = data_processor.get_voyage_data("", voyage_id)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")

        diagnosis = diagnosis_engine.diagnose_voyage(df, voyage_id, True)

        issues = diagnosis.issues
        if severity:
            issues = [i for i in issues if i.severity == severity]

        return {
            "voyage_id": voyage_id,
            "total_issues": len(issues),
            "severity_breakdown": {
                "high": len([i for i in diagnosis.issues if i.severity == "high"]),
                "medium": len([i for i in diagnosis.issues if i.severity == "medium"]),
                "low": len([i for i in diagnosis.issues if i.severity == "low"]),
            },
            "issues": issues,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ranking")
async def get_efficiency_ranking(limit: int = 10):
    try:
        all_voyages = data_processor.get_all_voyages()

        ranked_voyages = []
        for voyage in all_voyages:
            df = data_processor.get_voyage_data("", voyage.voyage_id)
            if df is not None:
                diagnosis = diagnosis_engine.diagnose_voyage(df, voyage.voyage_id, False)
                ranked_voyages.append(
                    {
                        "voyage_id": voyage.voyage_id,
                        "vessel_name": voyage.vessel_name,
                        "departure_port": voyage.departure_port,
                        "arrival_port": voyage.arrival_port,
                        "efficiency_score": diagnosis.overall_efficiency_score,
                        "total_fuel": voyage.total_fuel,
                        "total_distance": voyage.total_distance,
                        "fuel_efficiency": voyage.fuel_efficiency,
                        "issues_count": len(diagnosis.issues),
                        "potential_saving": diagnosis.total_potential_saving,
                    }
                )

        ranked_voyages.sort(key=lambda x: x["efficiency_score"], reverse=True)

        return {
            "total_voyages": len(ranked_voyages),
            "ranking": ranked_voyages[:limit],
            "average_score": round(
                sum(v["efficiency_score"] for v in ranked_voyages) / len(ranked_voyages), 2
            )
            if ranked_voyages
            else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_diagnosis_statistics():
    try:
        all_voyages = data_processor.get_all_voyages()

        issue_type_counts: dict = {}
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        total_potential_saving = 0
        scores = []

        for voyage in all_voyages:
            df = data_processor.get_voyage_data("", voyage.voyage_id)
            if df is not None:
                diagnosis = diagnosis_engine.diagnose_voyage(df, voyage.voyage_id, False)
                scores.append(diagnosis.overall_efficiency_score)
                total_potential_saving += diagnosis.total_potential_saving

                for issue in diagnosis.issues:
                    if issue.issue_type not in issue_type_counts:
                        issue_type_counts[issue.issue_type] = 0
                    issue_type_counts[issue.issue_type] += 1
                    severity_counts[issue.severity] += 1

        return {
            "total_voyages": len(scores),
            "average_efficiency_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "efficiency_distribution": {
                "excellent (>=90)": len([s for s in scores if s >= 90]),
                "good (75-89)": len([s for s in scores if 75 <= s < 90]),
                "fair (60-74)": len([s for s in scores if 60 <= s < 75]),
                "poor (<60)": len([s for s in scores if s < 60]),
            },
            "issue_type_breakdown": issue_type_counts,
            "severity_breakdown": severity_counts,
            "total_potential_saving": round(total_potential_saving, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
