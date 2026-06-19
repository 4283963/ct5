from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VesselDataPoint(BaseModel):
    timestamp: datetime
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    speed: float = Field(ge=0, le=40)
    fuel_consumption: float = Field(ge=0)
    wind_speed: float = Field(ge=0)
    wind_direction: float = Field(ge=0, le=360)
    course: float = Field(ge=0, le=360)
    engine_power: Optional[float] = None
    draft: Optional[float] = None


class UploadChunkRequest(BaseModel):
    file_id: str
    chunk_index: int
    total_chunks: int
    filename: str


class UploadChunkResponse(BaseModel):
    file_id: str
    chunk_index: int
    received: bool


class UploadCompleteRequest(BaseModel):
    file_id: str
    filename: str
    total_chunks: int


class UploadCompleteResponse(BaseModel):
    file_id: str
    status: str
    total_records: int
    voyage_ids: List[str]


class VoyageSummary(BaseModel):
    voyage_id: str
    vessel_name: str
    departure_port: str
    arrival_port: str
    start_time: datetime
    end_time: datetime
    total_distance: float
    total_fuel: float
    avg_speed: float
    fuel_efficiency: float


class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float


class VoyageMetrics(BaseModel):
    voyage_id: str
    speed_data: List[MetricDataPoint]
    fuel_data: List[MetricDataPoint]
    wind_data: List[MetricDataPoint]
    efficiency_data: List[MetricDataPoint]


class MetricsComparisonRequest(BaseModel):
    voyage_ids: List[str]
    metrics: List[str] = Field(default_factory=lambda: ["speed", "fuel", "wind", "efficiency"])


class MetricsComparisonResponse(BaseModel):
    voyage_ids: List[str]
    metrics: Dict[str, Dict[str, List[MetricDataPoint]]]
    summary: Dict[str, Dict[str, float]]


class InefficiencyIssue(BaseModel):
    issue_type: str
    severity: str
    description: str
    timestamp: Optional[datetime] = None
    location: Optional[Dict[str, float]] = None
    suggested_action: str
    potential_saving: float


class VoyageDiagnosis(BaseModel):
    voyage_id: str
    overall_efficiency_score: float
    issues: List[InefficiencyIssue]
    total_potential_saving: float
    optimization_summary: Dict[str, Any]


class DiagnosisRequest(BaseModel):
    voyage_id: str
    include_suggestions: bool = True


class BatchDiagnosisRequest(BaseModel):
    voyage_ids: List[str]
    include_suggestions: bool = True


class OptimizationSuggestion(BaseModel):
    category: str
    description: str
    expected_saving_percent: float
    implementation_difficulty: str
    priority: str


class OptimizationPlan(BaseModel):
    voyage_id: str
    baseline_efficiency: float
    target_efficiency: float
    suggestions: List[OptimizationSuggestion]
    total_expected_saving: float
    estimated_payback_period: Optional[str] = None


class FileInfo(BaseModel):
    file_id: str
    filename: str
    upload_time: datetime
    status: str
    total_records: int
    voyage_count: int


class VoyageListResponse(BaseModel):
    total: int
    voyages: List[VoyageSummary]
